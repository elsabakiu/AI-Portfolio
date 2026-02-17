class PromptTemplates:
    """Reusable prompt templates for personal branding LinkedIn content"""
    
    @staticmethod
    def thought_leadership():
        return """
        You are a personal branding expert creating LinkedIn content.
        
        {context}
        
        Topic: {topic}
        
        Create a Thought Leadership Post following this structure:
        
        HOOK: An attention-grabbing opening that challenges conventional thinking
        INSIGHT: A deep observation or pattern you've noticed in your work
        PERSONAL POV: Your unique perspective based on your experience
        ACTIONABLE TAKEAWAY: What your audience can do with this insight
        
        REQUIREMENTS:
        - Write in first-person (I, me, my)
        - Share real experience from context
        - Avoid generic advice
        - End with a question to engage
        
        Write the thought leadership post now:
        """
    
    @staticmethod
    def educational_post():
        return """
        You are a personal branding expert creating LinkedIn content.
        
        {context}
        
        Topic: {topic}
        
        Create an Educational Post following this structure:
        
        PROBLEM: A common challenge your audience faces
        EXPLANATION: Why this problem exists (based on your expertise)
        FRAMEWORK: A simple framework or step-by-step approach to solve it
        EXAMPLE: A real example applying the framework
        
        REQUIREMENTS:
        - Write in first-person (I, me, my)
        - Use specific examples from context
        - Make complex ideas simple
        - Include practical steps
        
        Write the educational post now:
        """
    
    @staticmethod
    def opinion_post():
        return """
        You are a personal branding expert creating LinkedIn content.
        
        {context}
        
        Topic: {topic}
        
        Create an Opinion / Commentary Post following this structure:
        
        TREND SUMMARY: Briefly describe what everyone is talking about
        YOUR STANCE: Where you stand on this topic (be clear)
        CONTRARIAN INSIGHT: A perspective that goes against the grain
        
        REQUIREMENTS:
        - Write in first-person (I, me, my)
        - Be specific about your disagreement
        - Back it up with experience from context
        - Be respectful but confident
        
        Write the opinion post now:
        """
    
    @staticmethod
    def uniqueness_check():
        return """
        Compare this generic AI content with our personal brand version:
        
        GENERIC LINKEDIN POST:
        {generic}
        
        OUR PERSONAL BRAND POST:
        {ours}
        
        Analyze the differences:
        1. Authenticity & personal voice:
        2. Specific examples vs generic advice:
        3. Engagement potential:
        """