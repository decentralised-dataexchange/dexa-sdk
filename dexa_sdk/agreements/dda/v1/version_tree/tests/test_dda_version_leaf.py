from asynctest import TestCase as AsyncTestCase
from asynctest import create_autospec
from ..version_tree import DDAVersionLeaf
from ...models.containers import DataDisclosureAgreementContainer


class TestDDAVersionLeaf(AsyncTestCase):
    """Test DDA Version Leaf Class"""

    async def test_dda_version_leaf_class(self) -> None:
        MockDataDisclosureAgreementContainer = create_autospec(
            DataDisclosureAgreementContainer)

        # Providing dda=None since TypeError exception was raised.
        # TypeError: missing a required argument: 'dda'
        # Expected this to be autospecced.
        dda_container = MockDataDisclosureAgreementContainer(dda=None)

        dda_version_leaf = DDAVersionLeaf(
            dda_container=dda_container,
            next_version_did="did:mydata:xyz",
            previous_version_did="did:mydata:abc"
        )

        assert isinstance(dda_version_leaf.dda_container,
                          DataDisclosureAgreementContainer)
        assert dda_version_leaf.next_version_did == "did:mydata:xyz"
        assert dda_version_leaf.previous_version_did == "did:mydata:abc"
