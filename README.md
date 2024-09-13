# GHIT (GitHub Issue Tools): A toolkit for GitHub Issues

## Instructions
> [!IMPORTANT]
> 
> You should have GitHub [Personal Access Token (PAT)](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)  

> [!WARNING]
> Make sure you have a good network connection to GitHub

> [!Note] 
> Before you start, clone the repo plz
> ```bash
> git clone https://github.com/NJU-iSE/GHIT.git
> ```
> then pip install the dependencies:
> ```bash
> pip install -r requirements.txt
>```
#### Quick Start
```bash
# collect the github issues from one specific repo
python main.py --config config/config.yaml main --processor collector --access_tokens ${ACCESS_TOKEN} --repo_name pytorch/pytorch
```
above command can collect all the issues from the repo `pytorch/pytorch`.  
Of course, you can collect issues from other repositories.  
plz change the `${ACCESS_TOKEN}` to your own access tokens  
the results would be saved in `Results/{repo_name}/all_issues.csv`  
```bash
# filter the issues by the given conditions (cleaner)
python main.py --config config/config.yaml main --processor cleaner --repo_name pytorch/pytorch
```
the filter results would be saved in `Results/{repo_name}/cleaned_issues.csv`  
you can change the filter conditions in the code (so sry that this is a dirty operation)

## TODO List
- [x] the config file needs to be refined
- [x] Implement basic tools
- [ ] use LLM to analyze the issues


## Project structure (ghit)
* processors (the module crawling/cleaning/counting data information from GitHub Issues)
  * tools
* analyzer
  * LDA
  * LLM
* utils


#### Future
- [ ] implement LLM analyzer
- [ ] test the System