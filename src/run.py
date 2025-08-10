import argparse
import uvicorn

from app import create_app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", default=8800, type=int)
    parser.add_argument("-ll", "--log_level", default="debug")
    args = parser.parse_args()

    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=args.port,
        log_level=args.log_level,
    )
