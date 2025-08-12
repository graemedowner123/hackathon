from app_dynamodb import app

# AWS Elastic Beanstalk looks for an 'application' object
application = app

if __name__ == "__main__":
    application.run()
