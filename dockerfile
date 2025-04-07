# Étape 1 : Construire l'application Angular
FROM node:18-alpine AS build
WORKDIR /app

# Copier package.json et package-lock.json, puis installer les dépendances
COPY package*.json ./
RUN npm install

# Copier le reste du projet et construire l'application
COPY . .
RUN npm run build --prod

# Étape 2 : Servir l'application avec Nginx
FROM nginx:alpine
COPY --from=build /app/dist/[ng-pokemon-app] /usr/share/nginx/html

# Copier la configuration Nginx personnalisée si nécessaire
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exposer le port 80
EXPOSE 80

# Lancer Nginx
CMD ["nginx", "-g", "daemon off;"]
