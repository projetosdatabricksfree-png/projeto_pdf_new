import inspect
from agentes.operarios.shared_tools.gwg.run_full_suite import _run_compression

source = inspect.getsource(_run_compression)
print(source)
