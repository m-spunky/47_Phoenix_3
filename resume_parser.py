import os
from json import JSONDecodeError
import PyPDF2
from dotenv import load_dotenv
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI
from langchain_community.llms import HuggingFaceEndpoint
from langchain_core.messages import BaseMessage
from pydantic import ValidationError
import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from resume_template import Resume


load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def pdf_to_string(file):
    """
    Convert a PDF file to a string.

    Parameters:
    file (io.BytesIO): A file-like object representing the PDF file. or file Path

    Returns:
    str: The extracted text from the PDF.
    """
    pdf_reader = PyPDF2.PdfReader(file)
    num_pages = len(pdf_reader.pages)
    text = ''
    for i in range(num_pages):
        page = pdf_reader.pages[i]
        text += page.extract_text()
    return text

class ResumeParser:
    def __init__(self, use_openai=False, openai_key=""):
        self.use_openai = use_openai
        self.openai_key = openai_key
        self.model = None
        self.set_model()
        self.skills = None

    def set_model(self):
        if self.use_openai:
            self.model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", max_tokens=2500, openai_api_key=self.openai_key)
        else:
            self.model = ChatGoogleGenerativeAI(model="gemini-pro",
                             temperature=0.3)
    def extract_resume_fields(self, full_text):
        """
        Analyze a resume text and extract structured information using a specified language model.

        Parameters:
        full_text (str): The text content of the resume.
        model (str): The language model object to use for processing the text.

        Returns:
        dict: A dictionary containing structured information extracted from the resume.
        """
        # The Resume object 
        with open("prompts/prompts_resume_extraction.prompt", "r") as f:
            template = f.read()

        with open("prompts/prompts_json.schema", "r") as f:
            json_schema = f.read()

        parser = PydanticOutputParser(pydantic_object=Resume)

        prompt_template = PromptTemplate(
            template=template,
            input_variables=["resume"],
            partial_variables={"response_template": json_schema},
        )

        formatted_input = prompt_template.format_prompt(resume=full_text)
        llm = self.model
       
        output = llm.invoke(formatted_input.to_string())
           
        import json
         # Print the output object for debugging
        if isinstance(output, BaseMessage):
            output = output.content
        try:
            parsed_output = parser.parse(output)
            
            json_output = parsed_output.json()
            data = json.loads(json_output)
            print(data["skills"])
            self.skills = data["skills"]
            
            return parsed_output

        except ValidationError as e:
            print(f"Validation error: {e}")
            #print(output)
            return output

        except JSONDecodeError as e:
            print(f"JSONDecodeError error: {e}")
            #print(output)
            return output

        except Exception as e:
            print(f"Exception: {e}")
            #print(output)
            return output

    def run(self, pdf_file_path):
        text = pdf_to_string(pdf_file_path)
        extracted_fields = self.extract_resume_fields(text)
        return extracted_fields

    def match_resume_with_job_description(self, resume_txt, job_description):
        with open("prompts/prompts_job_description_matching.prompt", "r") as f:
            template = f.read()

        prompt_template = PromptTemplate(
            template=template,
           input_variables=["resume", "job_description"],
        )
        # Invoke the language model and process the resume
        formatted_input = prompt_template.format_prompt(resume=resume_txt, job_description=job_description)
        llm = self.model
        output = llm.invoke(formatted_input.to_string())


        if isinstance(output, BaseMessage):
            output = output.content
        return output

    def recommendation_skill_based(self):
        """
        Analyze a skills and recommend course on basis of that.

        Parameters:
        skills (list):list of skills.
       
        Returns:
        dict: A dictionary containing structured information extracted web.
        """
        # The Resume object 
        with open("prompts/prompts_recommendation.prompt", "r") as f:
            template = f.read()

        prompt_template = PromptTemplate(
            template=template,
            input_variables=["skills"],
        )
        # Invoke the language model and process the resume
        skills = self.skills
        formatted_input = prompt_template.format_prompt(skills=skills)
        llm = self.model
       
        output = llm.invoke(formatted_input.to_string())

        return output


if __name__ == "__main__":
    p = ResumeParser(use_openai=False)
    res = p.run("samples/samples_0.pdf")
    # print(res)
