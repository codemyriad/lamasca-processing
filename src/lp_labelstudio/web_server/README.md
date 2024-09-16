## Running

This will start the backend in dev mode:

```bash
MODEL_DIR=/tmp/ label-studio-ml start src/lp_labelstudio/web_server/
```

The `MODEL_DIR` environment variable is there to make the sqlite3 file `cache.db` live in `/tmp`.
