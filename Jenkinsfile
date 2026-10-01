pipeline {
    agent any
    options {
        skipDefaultCheckout(true)
        timeout(time: 15, unit: 'MINUTES')
    }
    stages {
        stage('Clone Code') {
            steps {
                git branch: 'main', url: 'https://github.com/SUSHANK001-ops/DevOps-Project-Two-Tier-Flask-App.git'
            }
        }
        stage('Deploy with Docker Compose') {
            steps {
                sh '''
                    set -eu
                    docker compose down --remove-orphans || true
                    docker compose up -d --build --wait --wait-timeout 120
                    docker compose ps
                '''
            }
        }
    }
}