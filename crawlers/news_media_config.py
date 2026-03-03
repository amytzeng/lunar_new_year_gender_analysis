# Media configuration for news crawlers
# Defines domain names and CSS selectors for extracting article content

NEWS_MEDIA_CONFIG = {
    "cnn": {
        "domain": "cnn.com",
        "code": "cnn",
        "selectors": [
            "section[name='bodyText']",     # New CNN format
            "div.article__content",         # Old CNN format
            "div.l-container",              # Long-form articles
            "div.zn-body__paragraph",       # Alternative format
            "div.article-body",             # Generic article body
        ]
    },
    "abc_news": {
        "domain": "abcnews.go.com",
        "code": "abc",
        "selectors": [
            "div[data-module='ArticleBody']",    # New ABC News
            "div.ArticleBody",                   # Old ABC News
            "div.article-body",                  # Alternative version
            "div[data-testid='ArticleBody']",    # Test version
            "section[data-module='ArticleBody']", # Section format
            "div.article-content",               # Generic content block
            "div.content",                       # Generic content
        ]
    },
    "bbc": {
        "domain": "bbc.com",
        "code": "bbc",
        "selectors": [
            "article[data-testid='story-body']",  # Main article body
            "div[data-component='text-block']",   # Text blocks
            "div.story-body__inner",              # Story body inner
            "div.article-body",                   # Article body
            "div[property='articleBody']",        # Schema.org format
            "div.article__body",                  # Alternative format
        ]
    },
    "reuters": {
        "domain": "reuters.com",
        "code": "reuters",
        "selectors": [
            "div[data-testid='ArticleBody']",     # Main article body
            "div.article-body__content",          # Article body content
            "div.StandardArticleBody_body",       # Standard article body
            "div.ArticleBodyWrapper",             # Article body wrapper
            "p[data-testid='paragraph']",        # Paragraph elements
        ]
    },
    "ap_news": {
        "domain": "apnews.com",
        "code": "ap",
        "selectors": [
            "div.Article",                       # Article container
            "div[data-key='article-content']",   # Article content
            "div.RichTextStoryBody",             # Rich text story body
            "div.ArticleBody",                    # Article body
            "p.Component-root",                   # Component paragraphs
        ]
    },
    "guardian": {
        "domain": "theguardian.com",
        "code": "guardian",
        "selectors": [
            "div[data-gu-name='body']",          # Main body
            "div.article-body-commercial-selector", # Article body
            "div.content__article-body",         # Content article body
            "div[itemprop='articleBody']",      # Schema.org format
            "p[data-component='paragraph']",     # Paragraph components
        ]
    },
    "washington_post": {
        "domain": "washingtonpost.com",
        "code": "wp",
        "selectors": [
            "article[itemprop='articleBody']",   # Article body
            "div[data-qa='article-body']",      # Article body QA
            "div.article-body",                  # Article body
            "div[data-module='ArticleBody']",    # Article body module
            "div.pb-md",                         # Paragraph blocks
        ]
    },
    "nytimes": {
        "domain": "nytimes.com",
        "code": "nyt",
        "selectors": [
            "section[name='articleBody']",       # Article body section
            "div.StoryBodyCompanionColumn",      # Story body column
            "div[data-testid='article-body']",   # Article body test ID
            "p[class*='css-']",                  # CSS class paragraphs
            "div.article-body",                  # Article body
        ]
    },
    "nbc_news": {
        "domain": "nbcnews.com",
        "code": "nbc",
        "selectors": [
            "div.article-body__content",         # Article body content
            "div[data-module='ArticleBody']",    # Article body module
            "div.article-body",                  # Article body
            "div.story-body",                    # Story body
            "p[data-module='ArticleBody']",      # Paragraph module
        ]
    },
    "cbs_news": {
        "domain": "cbsnews.com",
        "code": "cbs",
        "selectors": [
            "div[data-module='ArticleBody']",    # Article body module
            "div.article-body",                  # Article body
            "div.content__body",                 # Content body
            "div.story-body",                    # Story body
            "p[data-module='ArticleBody']",      # Paragraph module
        ]
    },
    "fox_news": {
        "domain": "foxnews.com",
        "code": "fox",
        "selectors": [
            "div.article-body",                  # Article body
            "div[data-module='ArticleBody']",    # Article body module
            "div.story-body",                    # Story body
            "p[data-module='ArticleBody']",      # Paragraph module
            "div.article-content",               # Article content
        ]
    },
}

# Keywords for Lunar New Year related searches
LUNAR_NEW_YEAR_KEYWORDS = [
    "Lunar New Year",
    "Chinese New Year",
    "Spring Festival",
    "reunion dinner",
    "red envelope",
    "hongbao",
    "temple fair",
    "dragon dance",
    "lion dance",
    "returning to parents' home",
    "family reunion",
    "Chinese zodiac",
    "Year of the Horse",  # 2026 is Year of the Horse
    "lunar calendar",
    "Chinese traditions",
]
