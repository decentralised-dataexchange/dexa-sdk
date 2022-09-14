import semver
from asynctest import TestCase as AsyncTestCase
from dexa_sdk.utils.utils import bump_major_for_semver_string, paginate


class TestUtils(AsyncTestCase):
    """Test utils"""

    async def test_bump_major_for_semver_string(self):
        """Test bump major for semver string"""

        v1 = "1.0.0"
        v2 = bump_major_for_semver_string(v1)

        assert semver.compare(v1, v2) == -1

    async def test_paginate(self):
        """Test paginate"""

        items = [1, 2, 3, 4, 5]
        page = 1
        paginate_res = paginate(items, page, 1)

        # Test total pages after pagination
        assert paginate_res.pagination.get("total_pages") == 5
        # Test paginated result
        assert paginate_res.results == [1]

        # Invalid page returns empty result
        page = 6
        paginate_res = paginate(items, page, 1)

        assert paginate_res.results == []

        # Test last page result
        page = 5
        paginate_res = paginate(items, page, 1)

        assert paginate_res.results == [5]
