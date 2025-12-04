from app import app  # noqa: F401
from unified_api_endpoints import register_unified_apis

# Register unified APIs for Penora + ImageGene integration
register_unified_apis(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
