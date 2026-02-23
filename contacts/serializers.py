from rest_framework import serializers
from .models import Contact
import re

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"
    
    def validate_phone(self, value):
        """Custom validation for phone number"""
        # Remove special characters and keep only digits
        cleaned_phone = re.sub(r'\D', '', value)

        # if len(cleaned_phone) < 10:
        #     raise serializers.ValidationError("Phone number must have at least 10 digits.")

        # if len(cleaned_phone) == 10:
        #     cleaned_phone = f"91{cleaned_phone}"  # Add country code if needed

        # if not cleaned_phone.startswith("91") or len(cleaned_phone) != 12:
        #     raise serializers.ValidationError("Invalid phone number format. Must be 10 digits or 12 digits with '91'.")

        # return cleaned_phone

        # Define supported country codes and their lengths
        country_codes = {
            '91': 10,  # India: 91 + 10 digits
            '971': 9,  # UAE: 971 + 9 digits
            # Add more country codes as needed
        }
        
        # Check if the number already starts with a supported country code
        for code, length in country_codes.items():
            if cleaned_phone.startswith(code) and len(cleaned_phone) == len(code) + length:
                return cleaned_phone
        
        # If no country code detected, check if it's a valid local number
        if len(cleaned_phone) == 10:
            # Default to Indian number if no country code
            return f"91{cleaned_phone}"
        
        # If we reach here, the number format is not recognized
        valid_formats = [
            f"{code} + {length} digits" for code, length in country_codes.items()
        ]
        valid_formats.append("10 digits (will be prefixed with 91)")
        
        raise serializers.ValidationError(
            f"Invalid phone number format. Supported formats: {', '.join(valid_formats)}."
        )

