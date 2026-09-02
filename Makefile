.PHONY: all check test package serve-web

all: check

check:
	@PYTHONPATH=src python3 -m compileall -q src tests
	@PYTHONPATH=src python3 -c "from k5rx_tools import protocol, schema; assert protocol.crc16_ccitt(b'123456789') == 0x31C3; assert schema.CHANNEL_COUNT == 400"
	@PYTHONPATH=src python3 -c "import tempfile; from pathlib import Path; from k5rx_tools import csvio; d=tempfile.TemporaryDirectory(); p=Path(d.name)/'t.csv'; csvio.write_template(p); i=csvio.inspect(p); assert (i.memory_rows,i.bank_rows)==(400,8); d.cleanup()"
	@python3 -c "from pathlib import Path; h=Path('web/index.html').read_text(encoding='utf-8'); assert '<script>' in h and 'Write + Verify' in h and 'function templateCsv' in h and 'CSV雛形' in h"
	@echo "basic source checks passed"

test:
	uv run --extra dev pytest

package:
	uv build

serve-web:
	python3 -m http.server 8000 --directory web
