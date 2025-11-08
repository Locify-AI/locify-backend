from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class UserLocation(Base):
    """Tracks when users discover new cities/towns"""
    __tablename__ = "user_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    city_name = Column(String(255), index=True)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(String(255), nullable=True, index=True)
    
    # Relationship
    locations = relationship("Location", back_populates="user_location")


class Location(Base):
    """Stores historical locations discovered by the MCP agent"""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    fsq_id = Column(String(100), nullable=True, unique=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    distance = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    rating = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    popularity = Column(String(50), nullable=True)
    historical_significance = Column(Text, nullable=True)
    
    # Foreign key to user_location (which city/town this belongs to)
    user_location_id = Column(Integer, ForeignKey("user_locations.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_location = relationship("UserLocation", back_populates="locations")
    narration = relationship("Narration", back_populates="location", uselist=False)


class Narration(Base):
    """Stores generated tour guide narrations for locations"""
    __tablename__ = "narrations"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, unique=True, index=True)
    script = Column(Text, nullable=False)  # The 90-second narration script
    word_count = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    location = relationship("Location", back_populates="narration")

