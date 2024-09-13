## Running without Docker

Then you can start the ML backend:

```bash
label-studio-ml start src/lp_labelstudio/web_server/
```

# Configuration
Parameters can be set in `docker-compose.yml` before running the container.


The following common parameters are available:
- `BASIC_AUTH_USER` - specify the basic auth user for the model server
- `BASIC_AUTH_PASS` - specify the basic auth password for the model server
- `LOG_LEVEL` - set the log level for the model server
- `WORKERS` - specify the number of workers for the model server
- `THREADS` - specify the number of threads for the model server

# Customization

The ML backend can be customized by adding your own models and logic inside the `./dir_with_your_model` directory.
