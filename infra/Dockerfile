FROM nginx:1.22.1
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY nginx.conf /etc/nginx/conf.d
COPY ../frontend/build /usr/share/nginx/html/
COPY ../docs /usr/share/nginx/html/api/docs/