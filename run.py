"""Application entry point — factory pattern."""

from sscc import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
