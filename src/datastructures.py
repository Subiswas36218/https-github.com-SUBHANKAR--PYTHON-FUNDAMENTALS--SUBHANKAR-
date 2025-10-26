from typing import NamedTuple
from dataclasses import dataclass, field

# Named Tuple


class User(NamedTuple):
    id: int
    name: str
    email: str
    
    
    user=User(user_id=1, name="John Doe", email="email@site.com")
    
    
    # Dataclass
    @dataclass
    class DataClassUser:
        user_id: int
        username: str
        email: str
        is_active: bool = False
        tags: list[str] = field(default_factory=list)
        
        
        data_class_user=DataClassUser (id=2, name="Jane Doe", email=")