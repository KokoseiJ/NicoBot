node {
  stage('SCM') {
    checkout scm
  }
  environment {
    TOKEN = credentials('discord_test_token')
  }
  for (int i=6; i <= 10; i++) {
    stage("Test Python 3.${i}") {
      sh 'py3${i}/bin/python -m pip install -U pip pytest pytest-cov'
      sh 'py3${i}/bin/pytest --cov=discordapi --cov-report=xml:coverage-reports/discordapi_coverage-3.${i}.xml --junit-xml=xunit-reports/xunit-result-3.${i}.xml'
    }
  }
  stage('SonarQube Analysis') {
    def scannerHome = tool 'SonarScanner';
    withSonarQubeEnv() {
      sh "${scannerHome}/bin/sonar-scanner"
    }
  }
}
