"""Record the execution environment separately from mission/model settings."""
from functools import lru_cache
from importlib.metadata import version
import os
import platform
import sys
from pathlib import Path


@lru_cache(maxsize=1)
def runtime_environment():
    return dict(python=platform.python_version(),executable=sys.executable,
                system=platform.system(),machine=platform.machine(),libc=list(platform.libc_ver()),
                kernel=platform.release(),container=Path('/.dockerenv').exists(),
                runtime=os.environ.get('TRAJECTORY_RUNTIME','unspecified'),
                image_id=os.environ.get('TRAJECTORY_IMAGE_ID','unrecorded'),
                dependencies={name:version(name) for name in ('numpy','scipy','matplotlib','pandas','kiam-astro','daceypy','pillow')},
                thread_limits={key:os.environ.get(key) for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')})
