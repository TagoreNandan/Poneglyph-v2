import sys
import asyncio
sys.path.append('/Users/somespecies/Desktop/main projects/researchpilot for anti-gra')
from dotenv import load_dotenv
load_dotenv('.env')

from graph import generate_research

async def main():
    print("Testing Formula One pipeline")
    try:
        result = await generate_research("Formula One")
        print("Pipeline succeeded!")
        print(f"Report length: {len(result.get('report', ''))}")
        if result.get("report") == "Research generation could not be completed at this time.":
            print("FAILED WITH HARDCODED MESSAGE")
    except Exception as e:
        import traceback
        print(f"Pipeline crashed with exception: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
