import asyncio
import uuid
import concurrent.futures
from typing import Optional
from promptshield.config import ShieldConfig
from promptshield.detection.pipeline import run_pipeline
from promptshield.schemas.scan import ScanResponse

class Shield:
    def __init__(self, config: Optional[ShieldConfig] = None):
        self.config = config or ShieldConfig.load()

    def scan(self, prompt: str, context: Optional[str] = None) -> ScanResponse:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                result = pool.submit(asyncio.run, self._scan_async(prompt, context)).result()
        else:
            result = asyncio.run(self._scan_async(prompt, context))
            
        return result

    async def _scan_async(self, prompt: str, context: Optional[str] = None) -> ScanResponse:
        result_dict = await run_pipeline(prompt, self.config, context)
        return ScanResponse(
            scan_id=uuid.uuid4(),
            **result_dict
        )
