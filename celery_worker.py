from celery import Celery
import time
from google.cloud import translate_v2 as translate
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Create Celery app
celery = Celery('tasks', broker='redis://localhost:6379/0')

# Configure Celery
celery.conf.update(
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

translate_client = translate.Client()

@celery.task
def translate_text(text, target_lang='th'):
    try:
        result = translate_client.translate(text, target_language=target_lang)
        return result['translatedText']
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text  # Return original text if translation fails

@celery.task
def process_article(article):
    try:
        title = article['title']
        content = article.get('content') or article.get('summary', '')

        if not content.strip():
            content = "No content available for this article."

        print(f"Translating title: {title}")  # Debug print
        translated_title = translate_text(title)
        print(f"Translated title: {translated_title}")  # Debug print

        print(f"Translating content: {content[:100]}...")  # Debug print
        translated_content = translate_text(content)
        print(f"Translated content: {translated_content[:100]}...")  # Debug print

        return {
            'original_title': title,
            'original_content': content,
            'translated_title': translated_title,
            'translated_content': translated_content,
            'link': article['link']
        }
    except Exception as e:
        print(f"Error in process_article: {str(e)}")  # Debug print
        raise