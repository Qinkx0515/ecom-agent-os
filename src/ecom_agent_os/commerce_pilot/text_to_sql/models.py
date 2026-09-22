from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


class SQLGeneration(BaseModel):

    is_supported: bool

    query_plan: list[str] = Field(
        default_factory=list,
        max_length=6,
    )

    sql: str | None = None

    unsupported_reason: str | None = None

    @model_validator(
        mode="after"
    )
    def validate_consistency(
        self,
    ):

        if (
            self.is_supported
            and not self.sql
        ):
            raise ValueError(
                "sql is required when "
                "is_supported is true"
            )

        if (
            not self.is_supported
            and not self.unsupported_reason
        ):
            raise ValueError(
                "unsupported_reason is required "
                "when is_supported is false"
            )

        return self