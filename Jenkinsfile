pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.11'
        DOCKER_BUILDKIT = '1'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                echo "Code récupéré : ${env.GIT_BRANCH} @ ${env.GIT_COMMIT?.take(8)}"
            }
        }

        stage('Install') {
            parallel {
                stage('Install — backend-pays') {
                    steps {
                        dir('backend-pays') {
                            sh 'pip install -e ".[test,lint]"'
                        }
                    }
                }
                stage('Install — backend-central') {
                    steps {
                        dir('backend-central') {
                            sh 'pip install -e ".[test,lint]"'
                        }
                    }
                }
            }
        }

        stage('Lint') {
            parallel {
                stage('Ruff — pays') {
                    steps {
                        dir('backend-pays') {
                            sh 'ruff check app/ tests/'
                        }
                    }
                }
                stage('Ruff — central') {
                    steps {
                        dir('backend-central') {
                            sh 'ruff check app/ tests/'
                        }
                    }
                }
            }
        }

        stage('Tests — backend-pays') {
            steps {
                dir('backend-pays') {
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
                    cobertura coberturaReportFile: 'backend-pays/coverage.xml'
                }
            }
        }

        stage('Tests — backend-central') {
            steps {
                dir('backend-central') {
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
                }
            }
        }

        stage('Build Docker Images') {
            parallel {
                stage('Build backend-pays') {
                    steps {
                        sh 'docker build -t futurekawa/backend-pays:${GIT_COMMIT?.take(8) ?: "latest"} ./backend-pays'
                        sh 'docker tag futurekawa/backend-pays:${GIT_COMMIT?.take(8) ?: "latest"} futurekawa/backend-pays:latest'
                    }
                }
                stage('Build backend-central') {
                    steps {
                        sh 'docker build -t futurekawa/backend-central:${GIT_COMMIT?.take(8) ?: "latest"} ./backend-central'
                        sh 'docker tag futurekawa/backend-central:${GIT_COMMIT?.take(8) ?: "latest"} futurekawa/backend-central:latest'
                    }
                }
            }
        }

        stage('Archive') {
            steps {
                archiveArtifacts artifacts: 'backend-pays/coverage.xml, backend-central/coverage.xml', fingerprint: true
                echo "Images Docker construites : futurekawa/backend-pays:latest, futurekawa/backend-central:latest"
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
