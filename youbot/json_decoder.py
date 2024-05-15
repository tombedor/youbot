# import json
# import logging


# from langchain.prompts import ChatPromptTemplate

# from langchain_openai import ChatOpenAI


# MAX_DECODE_ATTEMPTS = 3

# llm = ChatOpenAI()


# def parse_json(input: str, attempts=0) -> dict:
#     try:
#         output = json.loads(input)
#         if attempts > 0:
#             logging.info(f"agent successfully correted JSON: attempt {attempts} of {MAX_DECODE_ATTEMPTS}")
#         return output
#     except json.decoder.JSONDecodeError as e:
#         if attempts >= MAX_DECODE_ATTEMPTS:
#             raise Exception("Too many attempts to decode JSON")
#         else:
#             logging.info("asking agent to correct JSON foramtting")

#         template = """
#         You are a helpful assistant who repairs malformed JSON.
#         You will receive text with the following information:

#         ERROR_MSG: The error message that was received when trying to parse the JSON.
    
#         INPUT: The malformed JSON.
    
#         Your response should contain nothing but properly formatted JSON.
#         """

#         human_template = """
#             ERROR_MSG: {error_msg}
            
#             INPUT: {input}
#             """

#         chat_prompt = ChatPromptTemplate.from_messages(
#             [
#                 ("system", template),
#                 ("human", human_template),
#             ]
#         )
#         chain = chat_prompt | llm

#         output = chain.invoke({"error_msg": e.msg, "input": input}).content
#         return parse_json(output, attempts + 1)


# if __name__ == "__main__":
#     print(parse_json('{"hello": "world'))
