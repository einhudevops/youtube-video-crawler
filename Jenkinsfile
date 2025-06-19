pipeline {
    agent any  // Use a generic agent

    environment {
        IMAGE_NAME = 'bhonebhone/yt-vd'
        K8S_NAMESPACE = "koyenaung"
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Set Image Tag') {
            steps {
                script {
                    def commit = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.IMAGE_TAG = commit
                    env.FULL_IMAGE = "${IMAGE_NAME}:${commit}"
                }
            }
        }

        stage('Install Python Dependencies') {
            steps {
                script {
                    // Install pip if not installed (using get-pip.py)
                    sh '''
                        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
                        python3 get-pip.py --user
                        rm get-pip.py
                    '''
                    // Install Python dependencies
                    sh 'pip3 install -r requirements.txt'
                }
            }
        }

        stage('Run Tests') {
            steps {
                sh 'pytest || true' // Run tests using pytest, continue even if tests fail
            }
        }

        stage('Build and Push Image (Buildah)') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-cred', usernameVariable: 'REG_USER', passwordVariable: 'REG_PASS')]) {
                    sh '''
                        echo "$REG_PASS" | sudo -S buildah login -u "$REG_USER" --password-stdin docker.io
                        sudo buildah bud -t $FULL_IMAGE .  // Build the Docker image
                        sudo buildah push $FULL_IMAGE // Push the image to Docker Hub
                    '''
                }
            }
        }

        stage('Update YAML and Push to GitHub (Trigger ArgoCD)') {
            steps {
                withCredentials([string(credentialsId: 'eihudevops', variable: 'GITHUB_TOKEN')]) {
                    sh '''
                        sed -i "s|image:.*|image: $FULL_IMAGE|" k8s/deployment.yaml

                        git config --global user.email "jenkins@ci.local"
                        git config --global user.name "Jenkins CI"

                        git add k8s/deployment.yaml
                        git commit -m "Update image to $FULL_IMAGE" || echo "No changes to commit"
                        
                        git remote set-url origin https://$GITHUB_TOKEN@github.com/einhudevops/youtube-video-crawler.git
                        git push origin HEAD:main
                    '''
                }
            }
        }
    }

    post {
        success {
            echo '✅ CI/CD Pipeline executed successfully!'
        }
        failure {
            echo '❌ Pipeline failed. Check logs for issues.'
        }
    }
}
