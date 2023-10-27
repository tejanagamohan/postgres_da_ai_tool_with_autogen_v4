import os
import autogen
from postgres_da_ai_agent.modules.db import PostgresManager
from postgres_da_ai_agent.agents import agent_config

# ----------------prompts------------



#create our terminate msg funtion
def is_termination_msg (content):
            have_content = content.get("content", None) is not None
            if have_content and "APPROVED" in content["content"] :
               return True
            return False    


COMPLETION_PROMPT = "If everything looks good, respond with APPROVED"

USER_PROXY_PROMPT = "A human admin, Interact with the Product Manager to discuss the plan. Plan execution needs to be approved by this admin." + COMPLETION_PROMPT
DATA_ENGINEER_PROMPT = "A Data Engineer. You follow an approved plan. Generate the initial SQL based on the requirement provided. Send it to the Sr Data Analyst for review" + COMPLETION_PROMPT
SR_DATA_ANALYST_PROMPT = "Sr Data Analyst. You follow an approved plan. You run the SQL query, generate the response and send it to the product manager for final review." + COMPLETION_PROMPT
PRODUCT_MANAGER_PROMPT = (
            "Product Manager. Validate the response to make sure it's correct" + COMPLETION_PROMPT
        )

TEXT_REPORT_ANALYST_PROMPT = "Text File Report Analyst. You exclusively use the write_file function on a summarized report."
JSON_REPORT_ANALYST_PROMPT = "Json  Report Analyst. You exclusively use the write_json_file function on a summarized report."
YML_REPORT_ANALYST_PROMPT = "Yaml Report Analyst. You exclusively use the write_yml_file function on a summarized report."




# ------------AGENTS------------


#create a set of agents with specific roles
#admin user proxy agent - takes in the prompt and manages the group chat

user_proxy = autogen.UserProxyAgent(
            name="Admin",
            system_message=USER_PROXY_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg,
        )
   

              # data engineer agent - generates the sql query

data_engineer = autogen.AssistantAgent(
            name="Engineer",
            llm_config=base_config,
            system_message=DATA_ENGINEER_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg,
        ) 
              # sr data analyst agent - run the sql query and generate the response

sr_data_analyst = autogen.AssistantAgent(
        
            name="Sr_Data_Analyst",
            llm_config= run_sql_config,
            system_message=SR_DATA_ANALYST_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg,
            function_map= function_map,
        )

def build_sr_data_analyst_agent(db: PostgresManager):
    return autogen.AssistantAgent(
            name = "Sr_Data_Analyst",
            llm_config = agent_config.run_sql_config,
            system_message = SR_DATA_ANALYST_PROMPT,
            code_execution_config = False,
            human_input_mode = "NEVER",
            function_map=agent_config.build_function_map_run_sql(db),
    )

              # product manager - validate the response to make sure it's correct

product_manager = autogen.AssistantAgent(
            name="Product_Manager",
            llm_config= base_config,
            system_message=PRODUCT_MANAGER_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg,
        )


 # text report analyst - writes a summary report of the results and saves them to a local text file

text_report_analyst = autogen.AssistantAgent(
            name="Text_Report_Analyst",
            llm_config=write_file_config,
            system_message=TEXT_REPORT_ANALYST_PROMPT,
            human_input_mode="NEVER",
            function_map=function_map_write_file,
        )
        
        # json report analyst - writes a summary report of the results and saves them to a json file
json_report_analyst = autogen.AssistantAgent(
            name="Json_Report_Analyst",
            llm_config=write_json_file_config,
            system_message=JSON_REPORT_ANALYST_PROMPT,
            human_input_mode="NEVER",
            function_map=function_map_write_json_file,
        )

yaml_report_analyst = autogen.AssistantAgent(
            name="Yml_Report_Analyst",
            llm_config=write_yaml_file_config,
            system_message=YML_REPORT_ANALYST_PROMPT,
            human_input_mode="NEVER",
            function_map=function_map_write_yaml_file,
        )


# ----------------orchestration----------

def build_team_orchestrator( 
        team: str, db: PostgresManager
) -> orchestrator.Orchestrator:
    if team == "data_eng":
      return orchestrator.Orchestrator(
           name="Postgres Data Analytics Multi-Agent ::: Data Engineering Team",
           agent=[
                user_proxy,
                data_engineer,
                build_sr_data_analyst_agent(db),
                product_manager,
           ],
      )
    elif team == "data_viz":
        return orchestrator.Orchestrator(
             name="Postgres Data Analytics Multi-Agent ::: Data Viz Team",
             agents=[
                  user_proxy,
                  text_report_analyst,
                  json_report_analyst,
                  yaml_report_analyst,
             ],
        )
   
