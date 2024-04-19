def pmpt_sys_init(
        lang: str
) -> str:
    return f"""
    You are an Machine learning engineer, and you are currently working on 
    an ML project using {lang} as the primary language. 
    
    You are asked to generate a script based on the user requirements.
    
    """
