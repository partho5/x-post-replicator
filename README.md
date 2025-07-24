# README.md

# Twitter Automation FastAPI Application

A comprehensive, modular FastAPI application for Twitter automation that scrapes tweets from source accounts, polishes them with AI, and posts them to your destination account.

## Features

- **Tweet Scraping**: Download recent tweets from any source account with media URLs
- **Media Management**: Download and store all associated media locally
- **AI Content Polishing**: Enhance tweet content using OpenAI API
- **Type-based Organization**: Classify and manage tweets by type (General, Promotional, News, etc.)
- **Duplicate Prevention**: Avoid posting duplicate content
- **SQLite Database**: Track all tweet metadata and status
- **RESTful API**: Complete FastAPI interface for all operations
- **Two-Account Architecture**: Scrape from source accounts, post to destination account (API keys)
- **Automated Workflow**: Complete end-to-end automation with step-by-step execution
- **Cron/Systemd Integration**: Ready for automated scheduling
- **Robust Error Handling**: Comprehensive error handling and logging

## Installation

1. Clone the repository:
```
git clone <repository-url>
cd twitter-automation
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Set up environment variables:
```
cp .env.example .env
# Edit .env with your API keys
```

4. Create required directories:
```
mkdir -p data/{raw_tweets,media,posted}
```

## Configuration

Update the `.env` file with your API credentials:

```env
# Twitter API Keys (Destination Account - Where you post to)
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Database
DATABASE_URL=sqlite:///./data/tweets.db
```

**Note:** The Twitter API keys determine which account you post to. You can scrape tweets from any public account, but you'll only post to the account associated with your API keys.

## Architecture

This application uses a **two-account architecture**:

- **Source Account**: The account you scrape tweets from (any public account)
- **Destination Account**: The account you post to (determined by your Twitter API keys in `.env`)

**Example:**
- Scrape tweets from `@jack98tom` (source account)
- Post polished tweets to your own account (destination account via API keys)

## Usage

1. Start the application:
```
uvicorn app.main:app --reload
```

2. Access the API documentation at `http://localhost:8000/docs`

### API Endpoints

#### Download Tweets
```
POST /tweets/download
{
    "username": "source_account",
    "count": 10
}
```

#### Post Tweets by Type
```
POST /tweets/post-by-type
{
    "tweet_type": 2,
    "limit": 5
}
```

#### Get Tweet Types
```
GET /tweets/types
```

#### Get User Tweets
```
GET /tweets/user/source_account?limit=10
```

#### Polish Tweet Content
```
POST /tweets/{tweet_id}/polish
```

#### Publish Latest Tweet
```
POST /tweets/publish-latest/{source_account}
```

#### Execute Complete Workflow
```
POST /workflow/execute
{
    "scrape_x_username": "source_account",
    "count": 1,
    "tweet_type": 2,
    "timeout": 60
}
```

**Parameters:**
- `scrape_x_username`: Account to scrape tweets from
- `count`: Number of tweets to process (default: 1)
- `tweet_type`: Specific tweet type to post (1-6, optional)
- `timeout`: Timeout per step in seconds (optional)

**Note:** Posts to destination account using API keys from `.env` file.

**Backward Compatibility:**
```
POST /workflow/execute
{
    "username": "source_account",  # Used for scraping only, posts to API key account
    "count": 1
}
```

#### Get Workflow Status
```
GET /workflow/status/{workflow_id}
```

#### Workflow Health Check
```
GET /workflow/health
```

## Tweet Types

- `1`: GENERAL - General content
- `2`: PROMOTIONAL - Marketing/promotional content
- `3`: NEWS - News and updates
- `4`: PERSONAL - Personal thoughts/experiences
- `5`: RETWEET - Retweets and shares
- `6`: THREAD - Thread content

## Automation

### Cron Jobs

Add to your crontab (`crontab -e`):

```bash
# Run every hour
0 * * * * cd /path/to/your/project && /path/to/your/venv/bin/python workflow_runner.py

# Run with specific parameters
0 * * * * cd /path/to/your/project && /path/to/your/venv/bin/python workflow_runner.py source_account 5 2
```

### Systemd Service

1. Copy the service files:
```bash
sudo cp systemd/twitter-workflow.service /etc/systemd/system/
sudo cp systemd/twitter-workflow.timer /etc/systemd/system/
```

2. Edit the service file with your paths:
```bash
sudo nano /etc/systemd/system/twitter-workflow.service
```

3. Enable and start the timer:
```bash
sudo systemctl daemon-reload
sudo systemctl enable twitter-workflow.timer
sudo systemctl start twitter-workflow.timer
```

### Environment Variables

Add these to your `.env` file for workflow automation:

```env
# Workflow Settings
WORKFLOW_DEFAULT_USERNAME=source_account_to_scrape
WORKFLOW_DEFAULT_COUNT=1
WORKFLOW_STEP_TIMEOUT=60
WORKFLOW_POSTING_TIMEOUT=1200
WORKFLOW_ENABLE_AUTO_POSTING=true
WORKFLOW_DEMO_MODE=false
```

**Demo Mode**: Set `WORKFLOW_DEMO_MODE=true` to use fake tweets for testing without hitting Twitter's API rate limits. When enabled, the workflow creates demo tweets instead of fetching real content.

## Architecture

The application follows a modular, class-based architecture with clear separation of concerns:

- **Routes**: FastAPI endpoints for API interface
- **Services**: Business logic for tweet operations
- **Database**: SQLite models and CRUD operations
- **AI**: OpenAI content polishing
- **Utils**: Logging, helpers, and utilities
- **Schemas**: Pydantic models for data validation

## File Structure

```
project_root/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Configuration settings
│   ├── database/                  # Database models and operations
│   ├── routes/                    # API endpoints
│   ├── services/                  # Business logic
│   ├── ai/openai/                 # AI content processing
│   ├── utils/                     # Utilities and helpers
│   ├── schemas/                   # Pydantic schemas
│   └── enums/                     # Enumerations
├── data/                          # Data storage
│   ├── raw_tweets/               # Original tweet data
│   ├── media/                    # Downloaded media files
│   └── posted/                   # Posted tweet records
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Error Handling

The application includes comprehensive error handling for:
- Twitter API rate limits
- Network timeouts
- Missing media files
- Database operations
- OpenAI API failures

## Logging

All operations are logged with appropriate levels:
- INFO: Normal operations
- WARNING: Potential issues
- ERROR: Actual failures

## Security

- API keys stored in environment variables
- No hardcoded credentials
- Proper error handling without exposing sensitive information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details
```

## Running the Application

To run the application:

```
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.
            
