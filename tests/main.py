from mle.integration import GithubInte

if __name__ == "__main__":
    inte = GithubInte("huangyz0918/termax")

    source_code = inte.process_source_code()
    commit_history = inte.process_commit_history()
    issues_prs = inte.process_issues_and_prs()
    print(source_code, commit_history, issues_prs)
