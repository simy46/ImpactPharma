from core.api_manager import OpenAIClient

client = OpenAIClient()

system_prompt = "I am testing the api..."
user_prompt = "Respond using the least number of tokens possible."

response = client.ask(system_prompt, user_prompt)
print(response)