from ..models.dda_models import DataDisclosureAgreementModel
from ..instances import DataDisclosureAgreementInstance
from ..base import BaseDataDisclosureAgreementTemplate


class DataDisclosureAgreementTemplate(BaseDataDisclosureAgreementTemplate):
    """
    Class for managing a data disclosure agreement template
    """

    def __init__(
        self,
        *,
        dda: DataDisclosureAgreementModel = None,
        did: str = None,
    ) -> None:
        """Initialise a new BaseDataDisclosureAgreementTemplate

        Args:
            dda (DataDisclosureAgreementModel): data disclosure agreement model. Defaults to None.
            did (str, optional): did:mydata identifier. Defaults to None.
        """

        self._dda = dda
        self._mydata_did = did
        self._merkle_tree = None

    def generate_dda_instance(self) -> DataDisclosureAgreementInstance:
        """Generate data disclosure agreement instance"""
        dda_instance = DataDisclosureAgreementInstance(dda=self.dda)
        return dda_instance
