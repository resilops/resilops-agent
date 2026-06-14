FROM nginx:latest
RUN apt-get update && apt-get install -y stress-ng
CMD ["nginx", "-g", "daemon off;"]
