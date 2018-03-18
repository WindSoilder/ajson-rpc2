''' type definition for the ajson-rpc2 lib internal use '''

from typing import (
    TypeVar, List, Mapping, Union,
    Optional, Any, Dict, Callable
)

JSON = TypeVar('JSON', List, Mapping)
