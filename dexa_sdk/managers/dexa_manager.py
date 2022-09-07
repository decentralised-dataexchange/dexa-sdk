import uuid
from loguru import logger
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.wallet.base import BaseWallet
from aries_cloudagent.wallet.indy import IndyWallet
from mydata_did.v1_0.utils.util import bool_to_str
from ..utils import (
    PaginationResult,
    paginate_records,
    drop_none_dict,
    bump_major_for_semver_string
)
from ..agreements.dda.v1_0.records.dda_template_record import (
    DataDisclosureAgreementTemplateRecord
)
from ..agreements.dda.v1_0.models.dda_models import (
    DDA_DEFAULT_CONTEXT,
    DDA_TYPE,
    DataDisclosureAgreementModel,
)


class DexaManager:
    """Manages Dexa related functions"""

    def __init__(self, context: InjectionContext) -> None:
        """Initialise Dexa manager

        Args:
            context (InjectionContext): Injection context to be used.
        """

        # Injection context
        self._context = context

        # Logger
        self._logger = logger

    @property
    def context(self) -> InjectionContext:
        """Accessor for injection context

        Returns:
            InjectionContext: Injection context
        """
        return self._context

    @property
    def logger(self):
        """Accessor for logger."""
        return self._logger

    async def create_and_store_dda_template_in_wallet(
            self,
            dda: dict,
            *,
            publish_flag: bool = True,
    ) -> DataDisclosureAgreementTemplateRecord:
        """Create and store dda template in wallet

        Args:
            dda (dict): DDA template.
            publish_flag (bool): Publish flag
            schema_id (str): Schema identifier
        """

        # Temp hack
        template_version = "1.0.0"
        template_id = str(uuid.uuid4())
        dda.update({"@context": DDA_DEFAULT_CONTEXT})
        dda.update({"@id": template_id})
        dda.update({"@type": DDA_TYPE})
        dda.update({"version": template_version})

        # Fetch wallet from context
        wallet: IndyWallet = await self.context.inject(BaseWallet)
        controller_did = await wallet.get_public_did()

        dda["dataController"].update({"did": f"did:sov:{controller_did.did}"})

        # Validate the data agreement.
        dda: DataDisclosureAgreementModel = \
            DataDisclosureAgreementModel.deserialize(
                dda)

        # Hack: Iterate through personal data records and add a unique identifier
        # Todo: Correlating personal data across agreements needs to be done.
        pds = dda.personal_data
        for pd in pds:
            pd.attribute_id = str(uuid.uuid4())

        # Update the personal data with attribute identifiers to the agreement
        dda.personal_data = pds

        # Create template record
        record = DataDisclosureAgreementTemplateRecord(
            template_id=template_id,
            template_version=template_version,
            state=DataDisclosureAgreementTemplateRecord.STATE_DEFINITION,
            data_disclosure_agreement=dda.serialize(),
            industry_sector=dda.data_sharing_restrictions.industry_sector.lower(),
            publish_flag=bool_to_str(publish_flag),
            latest_version_flag=bool_to_str(True)
        )

        await record.save(self.context)

        return record

    async def query_dda_templates_in_wallet(
        self,
        template_id: str = None,
        template_version: str = None,
        industry_sector: str = None,
        publish_flag: str = "false",
        delete_flag: str = "false",
        latest_version_flag: str = "false",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginationResult:
        """Query DA templates in wallet.

        Args:
            template_id (str, optional): Template id. Defaults to None.
            template_version (str, optional): Template version. Defaults to None.
            industry_sector (str, optional): Industry sector. Defaults to None.
            publish_flag (str, optional): Publish flag. Defaults to "false".
            delete_flag (str, optional): Delete flag. Defaults to "false".
            latest_version_flag (str, optional): Latest version flag. Defaults to "false".
            page (int): Page number. Defaults to 1.
            page_size (int): Page size. Defaults to 10.

        Returns:
            PaginationResult: Pagination result
        """

        # Query by version is only possible if the template id is provided
        if template_version:
            assert template_id, "Template identifier is required to query by version"

        # Tag filter
        tag_filter = {
            "template_id": template_id,
            "template_version": template_version,
            "industry_sector": industry_sector.lower() if industry_sector else industry_sector,
            "publish_flag": publish_flag,
            "delete_flag": delete_flag,
            "latest_version_flag": latest_version_flag
        }

        tag_filter = drop_none_dict(tag_filter)

        records = await DataDisclosureAgreementTemplateRecord.query(
            context=self.context,
            tag_filter=tag_filter
        )

        records = sorted(records, key=lambda k: k.created_at, reverse=True)

        paginate_result = paginate_records(records, page, page_size)

        return paginate_result

    async def update_dda_template_in_wallet(
        self,
        template_id: str,
        *,
        dda: dict,
        publish_flag: bool = True,
    ) -> DataDisclosureAgreementTemplateRecord:
        """Update DDA template in wallet.

        Args:
            template_id (str): Template identifier
            publish_flag (bool, optional): Publish flag. Defaults to True.

        Returns:
            DataDisclosureAgreementTemplateRecord: Upgraded template record.
        """

        # Fetch the latest template.
        existing_template = \
            await DataDisclosureAgreementTemplateRecord.latest_template_by_id(
                self.context,
                template_id
            )

        return await existing_template.upgrade(
            self.context,
            dda,
            bool_to_str(publish_flag)
        )

    async def delete_dda_template_in_wallet(
        self,
        template_id: str
    ):
        """Delete DDA template in wallet.

        Args:
            template_id (str): Template identifier.
        """

        # Fetch the latest template.
        existing_template = \
            await DataDisclosureAgreementTemplateRecord.latest_template_by_id(
                self.context,
                template_id
            )

        await existing_template.delete_template(self.context)

    async def publish_dda_template_wallet(
        self,
        template_id: str
    ):
        """Publish DDA template in wallet.

        Args:
            template_id (str): Template identifier
        """

        # Fetch the latest template.
        existing_template = \
            await DataDisclosureAgreementTemplateRecord.latest_template_by_id(
                self.context,
                template_id
            )

        await existing_template.publish_template(self.context)
