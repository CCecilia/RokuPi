import ipaddress
from PyInquirer import ValidationError, Validator


class IpAddressValidator(Validator):
    def validate(self, value):
        if len(value.text):
            try:
                if ipaddress.ip_address(value.text):
                    return True
                else:

                    raise ValidationError(
                        message="IP address needs to be in IPV4 format",
                        cursor_position=len(value.text))
            except ValueError:
                raise ValidationError(
                    message="IP address needs to be in IPV4 format",
                    cursor_position=len(value.text))
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))


class EmptyValidator(Validator):
    def validate(self, value):
        if len(value.text):
            return True
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))