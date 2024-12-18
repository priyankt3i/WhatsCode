import streamlit as st
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from github import Github

# Set up Streamlit app
st.title("GitHub Repository Analyzer")

# Initialize session state
if 'OPENAI_API_KEY' not in st.session_state:
    st.session_state.OPENAI_API_KEY = ''
if 'GITHUB_TOKEN' not in st.session_state:
    st.session_state.GITHUB_TOKEN = ''

# Input fields for API keys on the sidebar
st.sidebar.header("API Keys")
st.session_state.OPENAI_API_KEY = st.sidebar.text_input("OpenAI API Key", value=st.session_state.OPENAI_API_KEY)
st.session_state.GITHUB_TOKEN = st.sidebar.text_input("GitHub Token", value=st.session_state.GITHUB_TOKEN)

# Check if API keys are provided
if not st.session_state.OPENAI_API_KEY or not st.session_state.GITHUB_TOKEN:
    st.error("Please provide both OpenAI API Key and GitHub Token")
else:
    # Initialize OpenAI
    llm = OpenAI(openai_api_key=st.session_state.OPENAI_API_KEY)

    # Define a prompt template
    template = PromptTemplate(
        input_variables=["repo_url", "technologies"],
        template="""Assume you are a software developer, Analyze the repository at {repo_url} and generate a README 
                    with Overview section and also defines the technology stack used with setup and usage instructions, 
                    including prerequisites, installation steps, and example use cases. The technologies used are: {technologies}. 
                    Make sure the information is 100% correct and do not falsely provide any information that 
                    may not be accurate for the repository. Respond in Markdown language""",
    )

    # Create an LLM chain
    llm_chain = LLMChain(llm=llm, prompt=template)

    # Set up GitHub API with authentication
    g = Github(st.session_state.GITHUB_TOKEN)

    # Input field for GitHub repository URL
    repo_url = st.text_input("Enter GitHub repository URL (e.g., https://github.com/user/repo)")

    def extract_technologies(repo):
        technologies = set()
        for file in repo.get_contents(""):
            if file.type == "dir":
                for sub_file in repo.get_contents(file.path):
                    if sub_file.name.endswith((".py", ".js", ".java", ".cpp")):
                        technologies.add(sub_file.name.split(".")[-1])
            elif file.name.endswith((".py", ".js", ".java", ".cpp")):
                technologies.add(file.name.split(".")[-1])
        return list(technologies)

    def generate_readme(repo_url, technologies):
        # Generate README using LangChain
        response = llm_chain({"repo_url": repo_url, "technologies": ", ".join(technologies)})
        
        # Extract text from response dictionary
        report = response.get("text", "")

        # Extract relevant information from report
        lines = report.split("\n")
        prerequisites = []
        installation_steps = []
        example_use_cases = []

        for line in lines:
            if "Prerequisites:" in line:
                prerequisites.append(line.replace("Prerequisites:", "").strip())
            elif "Installation:" in line:
                installation_steps.append(line.replace("Installation:", "").strip())
            elif "Example Use Cases:" in line:
                example_use_cases.append(line.replace("Example Use Cases:", "").strip())

        # Create Markdown README
        markdown = f"""
# {repo_url.split('/')[-1]}
{report}
"""
        return markdown

    def analyze_repo(repo_url):
        try:
            # Extract repository owner and name from URL
            repo_owner = repo_url.split("/")[3]
            repo_name = repo_url.split("/")[4]

            # Get repository data from GitHub API
            repo = g.get_repo(f"{repo_owner}/{repo_name}")

            # Extract technologies used in the repository
            technologies = extract_technologies(repo)

            return repo, technologies
        except Exception as e:
            st.error(f"Error accessing repository: {e}")
            return None, None

    if st.button("Analyze Repository"):
        try:
            repo, technologies = analyze_repo(repo_url)
            if repo and technologies:
                readme = generate_readme(repo_url, technologies)
                st.markdown(readme)
        except Exception as e:
            st.error(f"Error: {e}")