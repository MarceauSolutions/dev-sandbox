"""
MCP Registry - Discovery and Management

Handles registration, discovery, and health monitoring of MCPs (Model Context Protocol servers).

Features:
- MCP registration and validation
- Discovery by category, capability, and search
- Health status tracking
- Rating and review management
- Developer management
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from database import Database, Row

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPStatus(Enum):
    """MCP lifecycle status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_REVIEW = "pending_review"


class ConnectivityType(Enum):
    """
    Connectivity types for MCPs.

    Allows registration of services that don't use traditional HTTP endpoints.
    """
    HTTP = "http"           # Standard REST API (default)
    EMAIL = "email"         # SMTP-based (send email, await response)
    OAUTH = "oauth"         # OAuth2 with token refresh
    WEBHOOK = "webhook"     # Inbound (they call us)
    GRAPHQL = "graphql"     # GraphQL queries
    ASYNC = "async"         # Long-running (hours/days)


class MCPCategory(Enum):
    """Service categories for MCPs"""
    RIDESHARE = "rideshare"
    FLIGHTS = "flights"
    HOTELS = "hotels"
    RESTAURANTS = "restaurants"
    FOOD_DELIVERY = "food_delivery"
    EVENTS = "events"
    SHOPPING = "shopping"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    UTILITIES = "utilities"
    OTHER = "other"


@dataclass
class MCPCapability:
    """A single capability offered by an MCP"""
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MCP:
    """Model Context Protocol server"""
    id: str
    developer_id: str
    name: str
    slug: str
    description: str
    category: MCPCategory
    version: str
    endpoint_url: Optional[str]  # Optional when connectivity_type != HTTP

    # Connectivity type (determines what endpoint fields are required)
    connectivity_type: ConnectivityType = ConnectivityType.HTTP

    # Alternative endpoints for non-HTTP connectivity types
    email_address: Optional[str] = None      # Required when connectivity_type == EMAIL
    webhook_path: Optional[str] = None       # Path for WEBHOOK type (we receive calls here)

    # Optional URLs
    health_check_url: Optional[str] = None
    documentation_url: Optional[str] = None

    # Pricing
    fee_per_request: float = 0.01
    developer_share: float = 0.80

    # Status
    status: MCPStatus = MCPStatus.PENDING_REVIEW

    # Quality metrics
    avg_response_time_ms: int = 0
    avg_rating: float = 0.0
    total_requests: int = 0
    total_errors: int = 0
    uptime_percent: float = 100.0

    # Metadata
    tags: List[str] = field(default_factory=list)
    supported_regions: List[str] = field(default_factory=list)
    rate_limit_rpm: int = 100
    timeout_ms: int = 30000

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None

    # Capabilities (loaded separately)
    capabilities: List[MCPCapability] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: Row) -> 'MCP':
        """Create MCP from database row"""
        import json

        # Parse JSON fields (stored as TEXT in SQLite)
        tags = row.get('tags', [])
        if isinstance(tags, str):
            tags = json.loads(tags) if tags else []

        regions = row.get('supported_regions', [])
        if isinstance(regions, str):
            regions = json.loads(regions) if regions else []

        # Parse connectivity_type (defaults to HTTP for backward compatibility)
        connectivity_type_str = row.get('connectivity_type', 'http')
        connectivity_type = ConnectivityType(connectivity_type_str) if connectivity_type_str else ConnectivityType.HTTP

        return cls(
            id=row['id'],
            developer_id=row['developer_id'],
            name=row['name'],
            slug=row['slug'],
            description=row.get('description', ''),
            category=MCPCategory(row['category']),
            version=row.get('version', '1.0.0'),
            endpoint_url=row.get('endpoint_url'),  # Now optional
            connectivity_type=connectivity_type,
            email_address=row.get('email_address'),
            webhook_path=row.get('webhook_path'),
            health_check_url=row.get('health_check_url'),
            documentation_url=row.get('documentation_url'),
            fee_per_request=float(row.get('fee_per_request', 0.01)),
            developer_share=float(row.get('developer_share', 0.80)),
            status=MCPStatus(row.get('status', 'pending_review')),
            avg_response_time_ms=int(row.get('avg_response_time_ms', 0)),
            avg_rating=float(row.get('avg_rating', 0.0)),
            total_requests=int(row.get('total_requests', 0)),
            total_errors=int(row.get('total_errors', 0)),
            uptime_percent=float(row.get('uptime_percent', 100.0)),
            tags=tags,
            supported_regions=regions,
            rate_limit_rpm=int(row.get('rate_limit_rpm', 100)),
            timeout_ms=int(row.get('timeout_ms', 30000)),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            last_health_check=row.get('last_health_check')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'developer_id': self.developer_id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'category': self.category.value,
            'version': self.version,
            'endpoint_url': self.endpoint_url,
            'connectivity_type': self.connectivity_type.value,
            'email_address': self.email_address,
            'webhook_path': self.webhook_path,
            'health_check_url': self.health_check_url,
            'documentation_url': self.documentation_url,
            'fee_per_request': self.fee_per_request,
            'developer_share': self.developer_share,
            'status': self.status.value,
            'avg_response_time_ms': self.avg_response_time_ms,
            'avg_rating': self.avg_rating,
            'total_requests': self.total_requests,
            'total_errors': self.total_errors,
            'uptime_percent': self.uptime_percent,
            'tags': self.tags,
            'supported_regions': self.supported_regions,
            'rate_limit_rpm': self.rate_limit_rpm,
            'timeout_ms': self.timeout_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'capabilities': [
                {
                    'name': cap.name,
                    'description': cap.description,
                    'input_schema': cap.input_schema,
                    'output_schema': cap.output_schema
                }
                for cap in self.capabilities
            ]
        }


@dataclass
class HealthCheckResult:
    """Result of an MCP health check"""
    mcp_id: str
    is_healthy: bool
    response_time_ms: int
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    checked_at: datetime = field(default_factory=datetime.now)


class MCPRegistry:
    """
    MCP Registry for discovery and management.

    Usage:
        registry = MCPRegistry(db)

        # Register a new MCP
        mcp_id = registry.register_mcp(
            developer_id='...',
            name='Weather Lookup',
            slug='weather-lookup',
            category=MCPCategory.UTILITIES,
            endpoint_url='http://localhost:8001/weather'
        )

        # Find MCPs
        mcps = registry.find_mcps(category=MCPCategory.RIDESHARE)

        # Get health status
        status = registry.get_health_status(mcp_id)

        # Update rating
        registry.update_rating(mcp_id, new_rating=4.5)
    """

    def __init__(self, db: Database):
        self.db = db

    # ==========================================
    # REGISTRATION
    # ==========================================

    def register_mcp(
        self,
        developer_id: str,
        name: str,
        slug: str,
        category: MCPCategory,
        endpoint_url: Optional[str] = None,
        connectivity_type: ConnectivityType = ConnectivityType.HTTP,
        email_address: Optional[str] = None,
        webhook_path: Optional[str] = None,
        description: str = "",
        health_check_url: Optional[str] = None,
        documentation_url: Optional[str] = None,
        fee_per_request: float = 0.01,
        developer_share: float = 0.80,
        tags: List[str] = None,
        supported_regions: List[str] = None,
        rate_limit_rpm: int = 100,
        timeout_ms: int = 30000,
        capabilities: List[MCPCapability] = None
    ) -> str:
        """
        Register a new MCP.

        Args:
            developer_id: Developer's UUID
            name: Human-readable name
            slug: URL-safe identifier (unique)
            category: Service category
            endpoint_url: Base URL for MCP API (required for HTTP/OAUTH/GRAPHQL)
            connectivity_type: How to connect to this MCP (default: HTTP)
            email_address: Email address for EMAIL type MCPs
            webhook_path: Our path to receive callbacks for WEBHOOK type
            description: Description of the MCP
            health_check_url: Optional health check endpoint
            documentation_url: Optional documentation URL
            fee_per_request: Price per API call (USD)
            developer_share: Fraction paid to developer (0.0-1.0)
            tags: Search tags
            supported_regions: Geographic regions served
            rate_limit_rpm: Requests per minute limit
            timeout_ms: Request timeout in ms
            capabilities: List of capabilities offered

        Returns:
            MCP ID (UUID)

        Raises:
            ValueError: If validation fails
        """
        import json

        # Validate
        self._validate_registration(
            developer_id=developer_id,
            name=name,
            slug=slug,
            endpoint_url=endpoint_url,
            connectivity_type=connectivity_type,
            email_address=email_address,
            webhook_path=webhook_path,
            fee_per_request=fee_per_request,
            developer_share=developer_share
        )

        # Check slug uniqueness
        existing = self.db.fetch_one(
            "SELECT id FROM mcps WHERE slug = ?",
            (slug,)
        )
        if existing:
            raise ValueError(f"Slug '{slug}' already exists")

        # Generate ID
        mcp_id = str(uuid.uuid4())

        # Prepare tags/regions as JSON for SQLite
        tags_json = json.dumps(tags or [])
        regions_json = json.dumps(supported_regions or ['global'])

        # Insert MCP
        self.db.execute(
            """
            INSERT INTO mcps (
                id, developer_id, name, slug, description, category,
                endpoint_url, connectivity_type, email_address, webhook_path,
                health_check_url, documentation_url,
                fee_per_request, developer_share, status,
                tags, supported_regions, rate_limit_rpm, timeout_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mcp_id, developer_id, name, slug, description, category.value,
                endpoint_url, connectivity_type.value, email_address, webhook_path,
                health_check_url, documentation_url,
                fee_per_request, developer_share, MCPStatus.PENDING_REVIEW.value,
                tags_json, regions_json, rate_limit_rpm, timeout_ms
            )
        )

        # Insert capabilities
        if capabilities:
            for cap in capabilities:
                self._add_capability(mcp_id, cap)

        # Initialize circuit breaker
        cb_id = str(uuid.uuid4())
        self.db.execute(
            """
            INSERT INTO circuit_breaker_state (id, mcp_id, state)
            VALUES (?, ?, 'closed')
            """,
            (cb_id, mcp_id)
        )

        logger.info(f"Registered MCP: {name} (id={mcp_id}, slug={slug})")
        return mcp_id

    def _validate_registration(
        self,
        developer_id: str,
        name: str,
        slug: str,
        endpoint_url: Optional[str],
        connectivity_type: ConnectivityType,
        email_address: Optional[str],
        webhook_path: Optional[str],
        fee_per_request: float,
        developer_share: float
    ):
        """Validate registration parameters based on connectivity type"""
        if not developer_id:
            raise ValueError("developer_id is required")

        if not name or len(name) < 3:
            raise ValueError("name must be at least 3 characters")

        if not slug or len(slug) < 3:
            raise ValueError("slug must be at least 3 characters")

        # Validate slug format (lowercase, hyphens, alphanumeric)
        import re
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', slug):
            raise ValueError("slug must be lowercase alphanumeric with hyphens")

        # Connectivity-type-specific validation
        if connectivity_type == ConnectivityType.HTTP:
            # HTTP requires a valid HTTP URL
            if not endpoint_url or not endpoint_url.startswith(('http://', 'https://')):
                raise ValueError("endpoint_url must be a valid HTTP URL for HTTP connectivity type")

        elif connectivity_type == ConnectivityType.EMAIL:
            # EMAIL requires an email address
            if not email_address:
                raise ValueError("email_address is required for EMAIL connectivity type")
            # Basic email format validation
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email_address):
                raise ValueError("email_address must be a valid email format")

        elif connectivity_type == ConnectivityType.WEBHOOK:
            # WEBHOOK requires a webhook path (our endpoint to receive calls)
            if not webhook_path:
                raise ValueError("webhook_path is required for WEBHOOK connectivity type")
            # Webhook path should start with /
            if not webhook_path.startswith('/'):
                raise ValueError("webhook_path must start with /")

        elif connectivity_type == ConnectivityType.OAUTH:
            # OAUTH requires an HTTP URL for token exchange
            if not endpoint_url or not endpoint_url.startswith(('http://', 'https://')):
                raise ValueError("endpoint_url must be a valid HTTP URL for OAUTH connectivity type")

        elif connectivity_type == ConnectivityType.GRAPHQL:
            # GRAPHQL requires an HTTP URL for the GraphQL endpoint
            if not endpoint_url or not endpoint_url.startswith(('http://', 'https://')):
                raise ValueError("endpoint_url must be a valid HTTP URL for GRAPHQL connectivity type")

        elif connectivity_type == ConnectivityType.ASYNC:
            # ASYNC is flexible - may use HTTP callback, email notification, or other
            # At minimum, we need some way to reach them (endpoint_url OR email_address)
            if not endpoint_url and not email_address:
                raise ValueError("ASYNC connectivity type requires either endpoint_url or email_address")

        if fee_per_request < 0:
            raise ValueError("fee_per_request cannot be negative")

        if not 0 <= developer_share <= 1:
            raise ValueError("developer_share must be between 0 and 1")

        # Check developer exists
        dev = self.db.fetch_one(
            "SELECT id FROM developers WHERE id = ?",
            (developer_id,)
        )
        if not dev:
            raise ValueError(f"Developer not found: {developer_id}")

    def _add_capability(self, mcp_id: str, capability: MCPCapability):
        """Add a capability to an MCP"""
        import json

        cap_id = str(uuid.uuid4())
        self.db.execute(
            """
            INSERT INTO mcp_capabilities (id, mcp_id, name, description, input_schema, output_schema, examples)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cap_id, mcp_id, capability.name, capability.description,
                json.dumps(capability.input_schema),
                json.dumps(capability.output_schema),
                json.dumps(capability.examples)
            )
        )

    def update_mcp(self, mcp_id: str, **updates) -> bool:
        """
        Update MCP fields.

        Args:
            mcp_id: MCP ID
            **updates: Fields to update

        Returns:
            True if updated, False if MCP not found
        """
        import json

        allowed_fields = {
            'name', 'description', 'endpoint_url', 'connectivity_type',
            'email_address', 'webhook_path', 'health_check_url',
            'documentation_url', 'fee_per_request', 'developer_share',
            'status', 'tags', 'supported_regions', 'rate_limit_rpm',
            'timeout_ms', 'version'
        }

        # Filter to allowed fields
        updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not updates:
            return False

        # Handle status enum
        if 'status' in updates and isinstance(updates['status'], MCPStatus):
            updates['status'] = updates['status'].value

        # Handle connectivity_type enum
        if 'connectivity_type' in updates and isinstance(updates['connectivity_type'], ConnectivityType):
            updates['connectivity_type'] = updates['connectivity_type'].value

        # Handle JSON fields
        if 'tags' in updates:
            updates['tags'] = json.dumps(updates['tags'])
        if 'supported_regions' in updates:
            updates['supported_regions'] = json.dumps(updates['supported_regions'])

        # Build query
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [mcp_id]

        rows_affected = self.db.execute(
            f"UPDATE mcps SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tuple(values)
        )

        return rows_affected > 0

    def activate_mcp(self, mcp_id: str) -> bool:
        """Activate an MCP (set status to active)"""
        return self.update_mcp(mcp_id, status=MCPStatus.ACTIVE)

    def suspend_mcp(self, mcp_id: str, reason: str = None) -> bool:
        """Suspend an MCP"""
        updated = self.update_mcp(mcp_id, status=MCPStatus.SUSPENDED)
        if updated:
            logger.warning(f"Suspended MCP {mcp_id}: {reason}")
        return updated

    def delete_mcp(self, mcp_id: str) -> bool:
        """
        Delete an MCP (hard delete).

        Also deletes: capabilities, circuit breaker state
        """
        # Delete capabilities
        self.db.execute(
            "DELETE FROM mcp_capabilities WHERE mcp_id = ?",
            (mcp_id,)
        )

        # Delete circuit breaker state
        self.db.execute(
            "DELETE FROM circuit_breaker_state WHERE mcp_id = ?",
            (mcp_id,)
        )

        # Delete MCP
        rows = self.db.execute(
            "DELETE FROM mcps WHERE id = ?",
            (mcp_id,)
        )

        if rows > 0:
            logger.info(f"Deleted MCP: {mcp_id}")
            return True
        return False

    # ==========================================
    # DISCOVERY
    # ==========================================

    def get_mcp(self, mcp_id: str) -> Optional[MCP]:
        """Get MCP by ID"""
        row = self.db.fetch_one(
            "SELECT * FROM mcps WHERE id = ?",
            (mcp_id,)
        )

        if not row:
            return None

        mcp = MCP.from_row(row)
        mcp.capabilities = self._get_capabilities(mcp_id)
        return mcp

    def get_mcp_by_slug(self, slug: str) -> Optional[MCP]:
        """Get MCP by slug"""
        row = self.db.fetch_one(
            "SELECT * FROM mcps WHERE slug = ?",
            (slug,)
        )

        if not row:
            return None

        mcp = MCP.from_row(row)
        mcp.capabilities = self._get_capabilities(mcp.id)
        return mcp

    def _get_capabilities(self, mcp_id: str) -> List[MCPCapability]:
        """Get capabilities for an MCP"""
        import json

        rows = self.db.fetch_all(
            "SELECT * FROM mcp_capabilities WHERE mcp_id = ?",
            (mcp_id,)
        )

        capabilities = []
        for row in rows:
            input_schema = row.get('input_schema', '{}')
            output_schema = row.get('output_schema', '{}')
            examples = row.get('examples', '[]')

            # Parse JSON if string
            if isinstance(input_schema, str):
                input_schema = json.loads(input_schema) if input_schema else {}
            if isinstance(output_schema, str):
                output_schema = json.loads(output_schema) if output_schema else {}
            if isinstance(examples, str):
                examples = json.loads(examples) if examples else []

            capabilities.append(MCPCapability(
                name=row['name'],
                description=row.get('description', ''),
                input_schema=input_schema,
                output_schema=output_schema,
                examples=examples
            ))

        return capabilities

    def find_mcps(
        self,
        category: Optional[MCPCategory] = None,
        status: MCPStatus = MCPStatus.ACTIVE,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        region: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_response_time_ms: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[MCP]:
        """
        Find MCPs matching criteria.

        Args:
            category: Filter by category
            status: Filter by status (default: active)
            search: Search name/description
            tags: Filter by tags (any match)
            region: Filter by supported region
            min_rating: Minimum average rating
            max_response_time_ms: Maximum response time
            limit: Maximum results
            offset: Skip first N results

        Returns:
            List of matching MCPs
        """
        conditions = []
        params = []

        # Status filter
        if status:
            conditions.append("status = ?")
            params.append(status.value)

        # Category filter
        if category:
            conditions.append("category = ?")
            params.append(category.value)

        # Search filter
        if search:
            conditions.append("(name LIKE ? OR description LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        # Tag filter (for SQLite, tags are JSON string)
        if tags:
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("tags LIKE ?")
                params.append(f'%"{tag}"%')
            conditions.append(f"({' OR '.join(tag_conditions)})")

        # Region filter
        if region:
            conditions.append("supported_regions LIKE ?")
            params.append(f'%"{region}"%')

        # Rating filter
        if min_rating is not None:
            conditions.append("avg_rating >= ?")
            params.append(min_rating)

        # Response time filter
        if max_response_time_ms is not None:
            conditions.append("avg_response_time_ms <= ?")
            params.append(max_response_time_ms)

        # Build query
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT * FROM mcps
            WHERE {where_clause}
            ORDER BY avg_rating DESC, total_requests DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        rows = self.db.fetch_all(query, tuple(params))
        return [MCP.from_row(row) for row in rows]

    def find_by_capability(self, capability_name: str) -> List[MCP]:
        """Find MCPs that offer a specific capability"""
        rows = self.db.fetch_all(
            """
            SELECT DISTINCT m.* FROM mcps m
            JOIN mcp_capabilities c ON m.id = c.mcp_id
            WHERE c.name = ? AND m.status = 'active'
            ORDER BY m.avg_rating DESC
            """,
            (capability_name,)
        )
        return [MCP.from_row(row) for row in rows]

    def list_categories(self) -> Dict[str, int]:
        """Get count of active MCPs per category"""
        rows = self.db.fetch_all(
            """
            SELECT category, COUNT(*) as count
            FROM mcps WHERE status = 'active'
            GROUP BY category
            ORDER BY count DESC
            """
        )
        return {row['category']: row['count'] for row in rows}

    # ==========================================
    # HEALTH MONITORING
    # ==========================================

    def get_health_status(self, mcp_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current health status for an MCP.

        Returns:
            Dict with health info or None if MCP not found
        """
        mcp = self.db.fetch_one(
            """
            SELECT id, name, status, avg_response_time_ms, uptime_percent,
                   total_requests, total_errors, last_health_check
            FROM mcps WHERE id = ?
            """,
            (mcp_id,)
        )

        if not mcp:
            return None

        # Get circuit breaker state
        cb = self.db.fetch_one(
            "SELECT state, failure_count FROM circuit_breaker_state WHERE mcp_id = ?",
            (mcp_id,)
        )

        # Get recent health checks
        recent_checks = self.db.fetch_all(
            """
            SELECT is_healthy, response_time_ms, checked_at
            FROM health_checks
            WHERE mcp_id = ?
            ORDER BY checked_at DESC
            LIMIT 10
            """,
            (mcp_id,)
        )

        # Calculate error rate
        error_rate = 0.0
        if mcp['total_requests'] > 0:
            error_rate = (mcp['total_errors'] / mcp['total_requests']) * 100

        return {
            'mcp_id': mcp_id,
            'name': mcp['name'],
            'status': mcp['status'],
            'is_healthy': mcp['status'] == 'active' and (not cb or cb['state'] == 'closed'),
            'circuit_breaker_state': cb['state'] if cb else 'closed',
            'failure_count': cb['failure_count'] if cb else 0,
            'avg_response_time_ms': mcp['avg_response_time_ms'],
            'uptime_percent': mcp['uptime_percent'],
            'error_rate_percent': round(error_rate, 2),
            'total_requests': mcp['total_requests'],
            'last_health_check': mcp['last_health_check'],
            'recent_checks': [
                {
                    'is_healthy': bool(check['is_healthy']),
                    'response_time_ms': check['response_time_ms'],
                    'checked_at': check['checked_at']
                }
                for check in recent_checks
            ]
        }

    def record_health_check(self, result: HealthCheckResult):
        """Record a health check result"""
        check_id = str(uuid.uuid4())

        self.db.execute(
            """
            INSERT INTO health_checks (id, mcp_id, checked_at, is_healthy, response_time_ms, status_code, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                check_id, result.mcp_id, result.checked_at,
                1 if result.is_healthy else 0,
                result.response_time_ms, result.status_code, result.error_message
            )
        )

        # Update MCP last health check
        self.db.execute(
            "UPDATE mcps SET last_health_check = ? WHERE id = ?",
            (result.checked_at, result.mcp_id)
        )

        # Update circuit breaker
        if result.is_healthy:
            self._record_success(result.mcp_id)
        else:
            self._record_failure(result.mcp_id, result.error_message)

    def _record_success(self, mcp_id: str):
        """Record successful request for circuit breaker"""
        self.db.execute(
            """
            UPDATE circuit_breaker_state
            SET success_count = success_count + 1,
                last_success_at = CURRENT_TIMESTAMP,
                failure_count = 0,
                state = 'closed',
                updated_at = CURRENT_TIMESTAMP
            WHERE mcp_id = ?
            """,
            (mcp_id,)
        )

    def _record_failure(self, mcp_id: str, error: str = None):
        """Record failed request for circuit breaker"""
        # Get current state
        cb = self.db.fetch_one(
            "SELECT state, failure_count FROM circuit_breaker_state WHERE mcp_id = ?",
            (mcp_id,)
        )

        if not cb:
            return

        new_failure_count = cb['failure_count'] + 1

        # Threshold: 5 failures in a row opens circuit
        if new_failure_count >= 5 and cb['state'] == 'closed':
            self.db.execute(
                """
                UPDATE circuit_breaker_state
                SET failure_count = ?,
                    last_failure_at = CURRENT_TIMESTAMP,
                    state = 'open',
                    opened_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE mcp_id = ?
                """,
                (new_failure_count, mcp_id)
            )
            logger.warning(f"Circuit breaker OPENED for MCP {mcp_id}: {error}")
        else:
            self.db.execute(
                """
                UPDATE circuit_breaker_state
                SET failure_count = ?,
                    last_failure_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE mcp_id = ?
                """,
                (new_failure_count, mcp_id)
            )

    # ==========================================
    # RATINGS
    # ==========================================

    def update_rating(self, mcp_id: str, new_rating: float) -> bool:
        """
        Update MCP's average rating.

        For simplicity, this sets the rating directly.
        In production, you'd track individual ratings and compute average.

        Args:
            mcp_id: MCP ID
            new_rating: New rating (0.0-5.0)

        Returns:
            True if updated
        """
        if not 0.0 <= new_rating <= 5.0:
            raise ValueError("Rating must be between 0.0 and 5.0")

        rows = self.db.execute(
            "UPDATE mcps SET avg_rating = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (round(new_rating, 2), mcp_id)
        )

        return rows > 0

    def increment_request_count(self, mcp_id: str, success: bool = True):
        """Increment request counter for an MCP"""
        if success:
            self.db.execute(
                """
                UPDATE mcps
                SET total_requests = total_requests + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (mcp_id,)
            )
            self._record_success(mcp_id)
        else:
            self.db.execute(
                """
                UPDATE mcps
                SET total_requests = total_requests + 1,
                    total_errors = total_errors + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (mcp_id,)
            )
            self._record_failure(mcp_id)

    def update_response_time(self, mcp_id: str, response_time_ms: int):
        """Update running average response time"""
        mcp = self.db.fetch_one(
            "SELECT avg_response_time_ms, total_requests FROM mcps WHERE id = ?",
            (mcp_id,)
        )

        if not mcp:
            return

        # Exponential moving average (weight recent more heavily)
        current_avg = mcp['avg_response_time_ms'] or response_time_ms
        new_avg = int(current_avg * 0.9 + response_time_ms * 0.1)

        self.db.execute(
            "UPDATE mcps SET avg_response_time_ms = ? WHERE id = ?",
            (new_avg, mcp_id)
        )

    # ==========================================
    # DEVELOPER MANAGEMENT
    # ==========================================

    def get_developer_mcps(self, developer_id: str) -> List[MCP]:
        """Get all MCPs for a developer"""
        rows = self.db.fetch_all(
            "SELECT * FROM mcps WHERE developer_id = ? ORDER BY created_at DESC",
            (developer_id,)
        )
        return [MCP.from_row(row) for row in rows]

    def get_developer_stats(self, developer_id: str) -> Dict[str, Any]:
        """Get aggregate stats for a developer"""
        stats = self.db.fetch_one(
            """
            SELECT
                COUNT(*) as mcp_count,
                SUM(total_requests) as total_requests,
                AVG(avg_rating) as avg_rating,
                AVG(uptime_percent) as avg_uptime
            FROM mcps
            WHERE developer_id = ?
            """,
            (developer_id,)
        )

        return {
            'developer_id': developer_id,
            'mcp_count': stats['mcp_count'] or 0,
            'total_requests': stats['total_requests'] or 0,
            'avg_rating': round(stats['avg_rating'] or 0, 2),
            'avg_uptime': round(stats['avg_uptime'] or 100, 2)
        }


# Example usage
if __name__ == "__main__":
    from database import create_test_database

    # Create test database
    db = create_test_database()

    # Add test developer
    dev_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO developers (id, email, display_name, api_key_hash) VALUES (?, ?, ?, ?)",
        (dev_id, 'test@example.com', 'Test Developer', 'hash123')
    )

    # Create registry
    registry = MCPRegistry(db)

    # Register MCP
    mcp_id = registry.register_mcp(
        developer_id=dev_id,
        name="Weather Lookup",
        slug="weather-lookup",
        category=MCPCategory.UTILITIES,
        endpoint_url="http://localhost:8001/weather",
        description="Get current weather for any location",
        tags=['weather', 'forecast', 'geolocation'],
        capabilities=[
            MCPCapability(
                name='current_weather',
                description='Get current weather conditions',
                input_schema={'type': 'object', 'properties': {'location': {'type': 'string'}}},
                output_schema={'type': 'object', 'properties': {'temperature': {'type': 'number'}}}
            )
        ]
    )

    print(f"Registered MCP: {mcp_id}")

    # Activate
    registry.activate_mcp(mcp_id)
    print("MCP activated")

    # Find MCPs
    mcps = registry.find_mcps(category=MCPCategory.UTILITIES)
    print(f"Found {len(mcps)} utility MCPs")

    # Get health status
    status = registry.get_health_status(mcp_id)
    print(f"Health status: {status}")

    # Update rating
    registry.update_rating(mcp_id, 4.5)
    print("Rating updated")

    # Get MCP
    mcp = registry.get_mcp(mcp_id)
    print(f"MCP: {mcp.name}, Rating: {mcp.avg_rating}")

    db.close()
