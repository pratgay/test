from google.cloud import translate_v3 as translate
import os

# Print the credentials path to ensure it's correct
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")

client = translate.TranslationServiceClient()

project_id = "total-pier-425200-f4"  # Replace with your actual project ID if different
location = "global"
parent = f"projects/{project_id}/locations/{location}"

text = "Hello, world!"

try:
    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",
            "source_language_code": "en-US",
            "target_language_code": "th",
        }
    )

    for translation in response.translations:
        print(f"Original text: {text}")
        print(f"Translated text: {translation.translated_text}")
except Exception as e:
    print(f"An error occurred: {str(e)}")