from __future__ import annotations

import time
from typing import Callable

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - friendly error at runtime
    serial = None
    list_ports = None

from . import protocol, schema

Progress = Callable[[str, int, int], None]


class RadioError(RuntimeError):
    pass


def available_ports() -> list[tuple[str, str]]:
    if list_ports is None:
        raise RadioError("pyserial is not installed")
    result: list[tuple[str, str]] = []
    for port in list_ports.comports():
        desc = " - ".join(x for x in (port.product, port.manufacturer) if x) or port.description or ""
        result.append((port.device, desc))
    return result


class K5Radio:
    def __init__(self, port: str, *, baud: int = 38400, timeout: float = 0.5) -> None:
        if serial is None:
            raise RadioError("pyserial is not installed")
        self.port_name = port
        self.baud = baud
        self.timeout = timeout
        self._serial = None
        self.session_id = protocol.new_session_id()
        self.version = ""

    def __enter__(self) -> "K5Radio":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def open(self) -> None:
        if self._serial is not None:
            return
        try:
            self._serial = serial.Serial(
                self.port_name,
                self.baud,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=self.timeout,
                write_timeout=2.0,
            )
        except serial.SerialException as exc:
            raise RadioError(f"cannot open serial port {self.port_name}: {exc}") from exc
        self._serial.reset_input_buffer()
        self.version = self.start_session()

    def close(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            finally:
                self._serial = None

    @property
    def ser(self):
        if self._serial is None:
            raise RadioError("radio is not open")
        return self._serial

    def _read_exact(self, size: int, deadline: float) -> bytes:
        data = bytearray()
        while len(data) < size:
            try:
                chunk = self.ser.read(size - len(data))
            except serial.SerialException as exc:
                raise RadioError(f"serial read failed: {exc}") from exc
            if chunk:
                data.extend(chunk)
                continue
            if time.monotonic() >= deadline:
                raise RadioError(f"serial receive timeout: wanted {size} bytes, got {len(data)}")
        return bytes(data)

    def _receive_frame(self, timeout: float) -> bytes:
        deadline = time.monotonic() + timeout
        previous = b""
        while True:
            byte = self._read_exact(1, deadline)
            if previous == b"\xAB" and byte == b"\xCD":
                break
            previous = byte
        size = int.from_bytes(self._read_exact(2, deadline), "little")
        if size > 512:
            raise RadioError(f"implausible serial frame size: {size}")
        body_and_tail = self._read_exact(size + 4, deadline)
        frame = protocol.FRAME_HEAD + size.to_bytes(2, "little") + body_and_tail
        try:
            return protocol.decode_frame(frame)
        except protocol.ProtocolError as exc:
            raise RadioError(str(exc)) from exc

    def request(self, payload: bytes, *, timeout: float = 4.0) -> bytes:
        frame = protocol.encode_frame(payload)
        try:
            self.ser.write(frame)
            self.ser.flush()
        except serial.SerialException as exc:
            raise RadioError(f"serial write failed: {exc}") from exc
        return self._receive_frame(timeout)

    def start_session(self) -> str:
        last_error: Exception | None = None
        for _attempt in range(5):
            try:
                self.ser.reset_input_buffer()
                reply = self.request(protocol.session_request(self.session_id), timeout=2.0)
                decoded = protocol.decode_payload(reply)
                if decoded.command_id == 0x0518:
                    raise RadioError("radio appears to be in firmware flash mode; start it normally")
                return protocol.parse_session_reply(reply)
            except (RadioError, protocol.ProtocolError) as exc:
                last_error = exc
        raise RadioError(f"session initialization failed: {last_error}")

    def read_eeprom(self, offset: int, size: int) -> bytes:
        if not 0 <= offset < schema.EEPROM_SIZE or not 1 <= size <= schema.READ_BLOCK or offset + size > schema.EEPROM_SIZE:
            raise RadioError("invalid EEPROM read range")
        reply = self.request(protocol.read_eeprom_request(offset, size, self.session_id), timeout=4.0)
        try:
            return protocol.parse_read_reply(reply, offset, size)
        except protocol.ProtocolError as exc:
            raise RadioError(str(exc)) from exc

    def write_eeprom(self, offset: int, data: bytes) -> None:
        if offset % schema.WRITE_BLOCK or len(data) % schema.WRITE_BLOCK:
            raise RadioError("EEPROM write must be aligned to 8-byte blocks")
        if not data or len(data) > schema.READ_BLOCK:
            raise RadioError("EEPROM write size must be 8..128 bytes")
        for block in range(offset, offset + len(data), schema.WRITE_BLOCK):
            if not schema.allowed_write_block(block):
                raise RadioError(f"write guard rejected 0x{block:04X}")
        reply = self.request(protocol.write_eeprom_request(offset, data, self.session_id), timeout=4.0)
        try:
            protocol.parse_write_reply(reply, offset)
        except protocol.ProtocolError as exc:
            raise RadioError(str(exc)) from exc

    def read_all(self, progress: Progress | None = None) -> bytes:
        out = bytearray(schema.EEPROM_SIZE)
        total = schema.EEPROM_SIZE
        for offset in range(0, total, schema.READ_BLOCK):
            size = min(schema.READ_BLOCK, total - offset)
            out[offset : offset + size] = self.read_eeprom(offset, size)
            if progress:
                progress("read", offset + size, total)
        return bytes(out)

    def write_image(
        self,
        new_image: bytes,
        *,
        base_image: bytes,
        progress: Progress | None = None,
        require_radio_matches_base: bool = True,
    ) -> int:
        schema.validate_image(base_image)
        schema.validate_image(new_image)
        blocks = schema.assert_safe_change(base_image, new_image)
        if not blocks:
            return 0

        if require_radio_matches_base:
            current = self.read_all(progress)
            if current != base_image:
                first = next(i for i, (a, b) in enumerate(zip(current, base_image, strict=True)) if a != b)
                raise RadioError(
                    f"radio no longer matches --base image; first difference at 0x{first:04X}. "
                    "Read a fresh backup and re-apply the intended changes."
                )

        chunks = schema.coalesce_blocks(blocks)
        total = len(chunks)
        for index, (start, end) in enumerate(chunks, start=1):
            wanted = new_image[start:end]
            self.write_eeprom(start, wanted)
            got = self.read_eeprom(start, len(wanted))
            if got != wanted:
                mismatch = next(i for i, (a, b) in enumerate(zip(got, wanted, strict=True)) if a != b)
                raise RadioError(f"verify failed at 0x{start + mismatch:04X}")
            if progress:
                progress("write", index, total)
        return len(chunks)
