properties([pipelineTriggers([githubPush()])])

pipeline {
  agent any
  environment {
    TOKEN = credentials('discord_test_token')
  }
  stages {
    stage('SCM') {
      checkout scm
    }
    for (int i=6; i <= 10; i++) {
      stage("Test Python 3.${i}") {
        sh "py3${i}/bin/python -m pip install -U pip pytest pytest-cov"
        sh "py3${i}/bin/pytest --cov=discordapi --cov-report=xml:coverage-reports/discordapi_coverage-3.${i}.xml --junit-xml=xunit-reports/xunit-result-3.${i}.xml"
      }
    }
    stage('SonarQube Analysis') {
      def scannerHome = tool 'SonarScanner';
      withSonarQubeEnv() {
        sh "${scannerHome}/bin/sonar-scanner"
      }
    }
  }
  post {
    always {
      discordSend webhookURL: "https://discord.com/api/webhooks/874596846230704128/F97_ST290jc9g6KO8aQVrT39OVdCiNwAGxuwI_7svUxOksVN7XgPwhf7A1jH_8yyOgdb", result: currentBuild.currentResult, link: env.BUILD_URL, thumbnail: "https://cdn.discordapp.com/avatars/874596846230704128/95765f559320a1bfdc0fec7866c3e332.webp?size=512", title: JOB_NAME
    }
  }
}
