pipeline {.
    agent none

    environment {
        DOCKER_BUILDKIT = '1'
        IMAGE_TAG = "${env.GIT_COMMIT ? env.GIT_COMMIT.take(8) : 'latest'}"
    }

    stages {

        stage('Checkout') {
            agent any
            steps {
                checkout scm
                echo "Code récupéré : ${env.GIT_BRANCH} @ ${env.GIT_COMMIT?.take(8)}"
            }
        }

        stage('backend-pays — lint & tests') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    args '-u root'
                }
            }
            steps {
                dir('backend-pays') {
                    sh 'pip install --no-cache-dir -e ".[test,lint]"'
                    sh 'ruff check app/ tests/'
                    sh '''
                        pytest tests/ \
                          --cov=app \
                          --cov-report=xml:coverage.xml \
                          --cov-report=term-missing \
                          --junitxml=test-results.xml \
                          -v
                    '''
                }
            }
            post {
                always {
                    junit 'backend-pays/test-results.xml'
                    archiveArtifacts artifacts: 'backend-pays/coverage.xml', fingerprint: true
                }
            }
        }

        stage('backend-central — lint & tests') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    args '-u root'
                }
            }
            steps {
                dir('backend-central') {
                    sh 'pip install --no-cache-dir -e ".[test,lint]"'
                    sh 'ruff check app/ tests/'
                    sh '''
                        pytest tests/ \
                          --cov=app \
                          --cov-report=xml:coverage.xml \
                          --cov-report=term-missing \
                          --junitxml=test-results.xml \
                          -v
                    '''
                }
            }
            post {
                always {
                    junit 'backend-central/test-results.xml'
                    archiveArtifacts artifacts: 'backend-central/coverage.xml', fingerprint: true
                }
            }
        }

        stage('Build Docker Images') {
            agent any
            steps {
                sh "docker build -t futurekawa/backend-pays:${IMAGE_TAG} ./backend-pays"
                sh "docker tag futurekawa/backend-pays:${IMAGE_TAG} futurekawa/backend-pays:latest"
                sh "docker build -t futurekawa/backend-central:${IMAGE_TAG} ./backend-central"
                sh "docker tag futurekawa/backend-central:${IMAGE_TAG} futurekawa/backend-central:latest"
                echo "Images construites : futurekawa/backend-pays:latest, futurekawa/backend-central:latest"
            }
        }
    }

    post {
        failure {
            echo "Pipeline échoué sur la branche ${env.GIT_BRANCH}"
        }
        success {
            echo "Pipeline réussi — solution prête pour la démo"
        }
    }
}
