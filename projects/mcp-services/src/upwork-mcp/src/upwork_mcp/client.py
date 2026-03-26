"""Upwork API Client with OAuth 2.0 authentication."""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass

import upwork
from upwork import Config

logger = logging.getLogger(__name__)


@dataclass
class UpworkCredentials:
    """Upwork API credentials."""
    client_id: str
    client_secret: str
    redirect_uri: str = "https://localhost"
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[float] = None


class UpworkClient:
    """
    Upwork API client wrapper with OAuth 2.0 support.

    Handles authentication, token refresh, and API requests.
    """

    def __init__(self, credentials: Optional[UpworkCredentials] = None):
        """
        Initialize Upwork client.

        Args:
            credentials: UpworkCredentials object. If None, loads from environment.
        """
        self.credentials = credentials or self._load_credentials_from_env()
        self._client: Optional[upwork.Client] = None
        self._token_path = Path.home() / ".upwork" / "token.json"

    def _load_credentials_from_env(self) -> UpworkCredentials:
        """Load credentials from environment variables."""
        return UpworkCredentials(
            client_id=os.getenv("UPWORK_CLIENT_ID", ""),
            client_secret=os.getenv("UPWORK_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("UPWORK_REDIRECT_URI", "https://localhost"),
            access_token=os.getenv("UPWORK_ACCESS_TOKEN"),
            refresh_token=os.getenv("UPWORK_REFRESH_TOKEN"),
        )

    def _load_saved_token(self) -> Optional[dict]:
        """Load saved token from disk."""
        if self._token_path.exists():
            try:
                with open(self._token_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load saved token: {e}")
        return None

    def _save_token(self, token: dict) -> None:
        """Save token to disk."""
        self._token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._token_path, "w") as f:
            json.dump(token, f)
        logger.info(f"Token saved to {self._token_path}")

    def get_authorization_url(self) -> str:
        """
        Get OAuth authorization URL for user consent.

        Returns:
            URL to redirect user for authorization.
        """
        config = Config({
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
            "redirect_uri": self.credentials.redirect_uri,
        })
        client = upwork.Client(config)
        return client.get_authorization_url()

    def complete_authorization(self, authorization_response: str) -> dict:
        """
        Complete OAuth flow with authorization response.

        Args:
            authorization_response: The full callback URL with auth code.

        Returns:
            Token dictionary with access_token, refresh_token, etc.
        """
        config = Config({
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
            "redirect_uri": self.credentials.redirect_uri,
        })
        client = upwork.Client(config)
        token = client.get_access_token(authorization_response)
        self._save_token(token)
        return token

    def _get_client(self) -> upwork.Client:
        """Get authenticated Upwork client."""
        if self._client is not None:
            return self._client

        # Try to load saved token first
        saved_token = self._load_saved_token()

        # Build token config
        token_config = {}
        if saved_token:
            token_config = saved_token
        elif self.credentials.access_token:
            token_config = {
                "access_token": self.credentials.access_token,
                "refresh_token": self.credentials.refresh_token,
                "token_type": "Bearer",
            }

        if not token_config.get("access_token"):
            raise ValueError(
                "No access token available. Run authorization flow first:\n"
                f"1. Visit: {self.get_authorization_url()}\n"
                "2. Complete OAuth and provide the callback URL"
            )

        config = Config({
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
            "redirect_uri": self.credentials.redirect_uri,
            "token": token_config,
        })

        self._client = upwork.Client(config)
        return self._client

    def graphql(self, query: str, variables: Optional[dict] = None) -> dict:
        """
        Execute GraphQL query against Upwork API.

        Args:
            query: GraphQL query string
            variables: Optional variables for the query

        Returns:
            Query response as dictionary
        """
        client = self._get_client()

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = client.post(
            "/api/graphql/v1",
            payload,
        )
        return response

    def rest_get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """
        Make REST GET request to Upwork API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response as dictionary
        """
        client = self._get_client()
        return client.get(endpoint, params or {})

    def rest_post(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """
        Make REST POST request to Upwork API.

        Args:
            endpoint: API endpoint path
            data: Request body data

        Returns:
            Response as dictionary
        """
        client = self._get_client()
        return client.post(endpoint, data or {})

    def is_authenticated(self) -> bool:
        """Check if client has valid authentication."""
        try:
            self._get_client()
            return True
        except ValueError:
            return False


# GraphQL Queries
SEARCH_JOBS_QUERY = """
query SearchJobs($query: String!, $limit: Int, $offset: Int) {
    marketplaceJobPostings(
        searchExpression_eq: $query
        pagination: { limit: $limit, offset: $offset }
    ) {
        edges {
            node {
                id
                title
                description
                budget {
                    amount
                    currencyCode
                }
                hourlyBudget {
                    min
                    max
                }
                duration
                experienceLevel
                publishedDateTime
                client {
                    totalPostedJobs
                    totalHires
                    totalSpend {
                        amount
                    }
                    paymentVerificationStatus
                    location {
                        country
                    }
                }
                skills {
                    name
                }
            }
        }
        totalCount
    }
}
"""

JOB_DETAILS_QUERY = """
query JobDetails($jobId: ID!) {
    marketplaceJobPosting(id: $jobId) {
        id
        title
        description
        budget {
            amount
            currencyCode
        }
        hourlyBudget {
            min
            max
        }
        duration
        experienceLevel
        publishedDateTime
        proposalsTier
        inviteOnly
        client {
            totalPostedJobs
            totalHires
            totalSpend {
                amount
            }
            paymentVerificationStatus
            location {
                country
            }
            companyName
            companyDescription
        }
        skills {
            name
        }
        questions {
            question
        }
        attachments {
            name
            url
        }
    }
}
"""

MY_PROFILE_QUERY = """
query MyProfile {
    me {
        id
        name
        email
        freelancerProfile {
            title
            overview
            hourlyRate {
                amount
                currencyCode
            }
            skills {
                name
            }
            portfolioItems {
                title
                description
            }
            stats {
                totalJobs
                totalHours
                totalEarnings {
                    amount
                }
            }
        }
    }
}
"""

MY_PROPOSALS_QUERY = """
query MyProposals($status: ProposalStatus, $limit: Int) {
    proposals(status_eq: $status, pagination: { limit: $limit }) {
        edges {
            node {
                id
                status
                createdDateTime
                job {
                    id
                    title
                    client {
                        companyName
                    }
                }
                coverLetter
                chargedAmount {
                    amount
                }
            }
        }
        totalCount
    }
}
"""

MY_CONTRACTS_QUERY = """
query MyContracts($status: ContractStatus, $limit: Int) {
    contracts(status_eq: $status, pagination: { limit: $limit }) {
        edges {
            node {
                id
                status
                title
                startDateTime
                endDateTime
                totalEarnings {
                    amount
                }
                client {
                    companyName
                    location {
                        country
                    }
                }
                feedback {
                    score
                    comment
                }
            }
        }
        totalCount
    }
}
"""
