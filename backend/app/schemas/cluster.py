from enum import Enum

class StrategicCluster(str, Enum):
    """The 5 strategic clusters being monitored."""
    PRICING_PROMOTIONS = "Pricing, Promotions & Retail Media"
    LOGISTICS_FULFILLMENT = "Logistics, Fulfillment & Expansion"
    PRODUCT_ECOSYSTEM = "Product, AI & Platform Ecosystem"
    MARKETPLACE_SELLER = "Marketplace & Seller Operations"
    CORPORATE_STRATEGY = "Corporate Strategy, M&A & Workforce"
