use the args in teh react docker file to place the env at the compile time since nginx serve teh compiled build it does take teh secrets and config at the run time like fastapi

When you define env: in your Deployment and reference a ConfigMap or Secret, Kubernetes injects those values into the container’s environment.

Backend frameworks (FastAPI, Node.js, Spring Boot) naturally consume them at runtime.

Frontend frameworks (React+Vite) do not — they require build-time injection or a runtime config file workaround.
