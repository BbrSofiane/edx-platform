"""
Test instructor.access
"""


import pytest
from six.moves import range

from lms.djangoapps.instructor.access import allow_access, list_with_level, revoke_access, update_forum_role
from openedx.core.djangoapps.ace_common.tests.mixins import EmailTemplateTagMixin
from openedx.core.djangoapps.django_comment_common.models import FORUM_ROLE_MODERATOR, Role
from common.djangoapps.student.roles import CourseBetaTesterRole, CourseCcxCoachRole, CourseStaffRole
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestInstructorAccessList(SharedModuleStoreTestCase):
    """ Test access listings. """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorAccessList, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestInstructorAccessList, self).setUp()  # lint-amnesty, pylint: disable=super-with-arguments
        self.instructors = [UserFactory.create() for _ in range(4)]
        for user in self.instructors:
            allow_access(self.course, user, 'instructor')
        self.beta_testers = [UserFactory.create() for _ in range(4)]
        for user in self.beta_testers:
            allow_access(self.course, user, 'beta')

    def test_list_instructors(self):
        instructors = list_with_level(self.course, 'instructor')
        self.assertEqual(set(instructors), set(self.instructors))

    def test_list_beta(self):
        beta_testers = list_with_level(self.course, 'beta')
        self.assertEqual(set(beta_testers), set(self.beta_testers))


class TestInstructorAccessAllow(EmailTemplateTagMixin, SharedModuleStoreTestCase):
    """ Test access allow. """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorAccessAllow, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestInstructorAccessAllow, self).setUp()  # lint-amnesty, pylint: disable=super-with-arguments

        self.course = CourseFactory.create()

    def test_allow(self):
        user = UserFactory()
        allow_access(self.course, user, 'staff')
        self.assertTrue(CourseStaffRole(self.course.id).has_user(user))

    def test_allow_twice(self):
        user = UserFactory()
        allow_access(self.course, user, 'staff')
        allow_access(self.course, user, 'staff')
        self.assertTrue(CourseStaffRole(self.course.id).has_user(user))

    def test_allow_ccx_coach(self):
        user = UserFactory()
        allow_access(self.course, user, 'ccx_coach')
        self.assertTrue(CourseCcxCoachRole(self.course.id).has_user(user))

    def test_allow_beta(self):
        """ Test allow beta against list beta. """
        user = UserFactory()
        allow_access(self.course, user, 'beta')
        self.assertTrue(CourseBetaTesterRole(self.course.id).has_user(user))

    def test_allow_badlevel(self):
        user = UserFactory()
        with pytest.raises(ValueError):
            allow_access(self.course, user, 'robot-not-a-level')

    def test_allow_noneuser(self):
        user = None
        with pytest.raises(Exception):
            allow_access(self.course, user, 'staff')


class TestInstructorAccessRevoke(SharedModuleStoreTestCase):
    """ Test access revoke. """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorAccessRevoke, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestInstructorAccessRevoke, self).setUp()  # lint-amnesty, pylint: disable=super-with-arguments
        self.staff = [UserFactory.create() for _ in range(4)]
        for user in self.staff:
            allow_access(self.course, user, 'staff')
        self.beta_testers = [UserFactory.create() for _ in range(4)]
        for user in self.beta_testers:
            allow_access(self.course, user, 'beta')

    def test_revoke(self):
        user = self.staff[0]
        revoke_access(self.course, user, 'staff')
        self.assertFalse(CourseStaffRole(self.course.id).has_user(user))

    def test_revoke_twice(self):
        user = self.staff[0]
        revoke_access(self.course, user, 'staff')
        self.assertFalse(CourseStaffRole(self.course.id).has_user(user))

    def test_revoke_beta(self):
        user = self.beta_testers[0]
        revoke_access(self.course, user, 'beta')
        self.assertFalse(CourseBetaTesterRole(self.course.id).has_user(user))

    def test_revoke_badrolename(self):
        user = UserFactory()
        with pytest.raises(ValueError):
            revoke_access(self.course, user, 'robot-not-a-level')


class TestInstructorAccessForum(SharedModuleStoreTestCase):
    """
    Test forum access control.
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorAccessForum, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestInstructorAccessForum, self).setUp()  # lint-amnesty, pylint: disable=super-with-arguments
        self.mod_role = Role.objects.create(
            course_id=self.course.id,
            name=FORUM_ROLE_MODERATOR
        )
        self.moderators = [UserFactory.create() for _ in range(4)]
        for user in self.moderators:
            self.mod_role.users.add(user)

    def test_allow(self):
        user = UserFactory.create()
        update_forum_role(self.course.id, user, FORUM_ROLE_MODERATOR, 'allow')
        self.assertIn(user, self.mod_role.users.all())

    def test_allow_twice(self):
        user = UserFactory.create()
        update_forum_role(self.course.id, user, FORUM_ROLE_MODERATOR, 'allow')
        self.assertIn(user, self.mod_role.users.all())
        update_forum_role(self.course.id, user, FORUM_ROLE_MODERATOR, 'allow')
        self.assertIn(user, self.mod_role.users.all())

    def test_allow_badrole(self):
        user = UserFactory.create()
        with pytest.raises(Role.DoesNotExist):
            update_forum_role(self.course.id, user, 'robot-not-a-real-role', 'allow')

    def test_revoke(self):
        user = self.moderators[0]
        update_forum_role(self.course.id, user, FORUM_ROLE_MODERATOR, 'revoke')
        self.assertNotIn(user, self.mod_role.users.all())

    def test_revoke_twice(self):
        user = self.moderators[0]
        update_forum_role(self.course.id, user, FORUM_ROLE_MODERATOR, 'revoke')
        self.assertNotIn(user, self.mod_role.users.all())
        update_forum_role(self.course.id, user, FORUM_ROLE_MODERATOR, 'revoke')
        self.assertNotIn(user, self.mod_role.users.all())

    def test_revoke_notallowed(self):
        user = UserFactory()
        update_forum_role(self.course.id, user, FORUM_ROLE_MODERATOR, 'revoke')
        self.assertNotIn(user, self.mod_role.users.all())

    def test_revoke_badrole(self):
        user = self.moderators[0]
        with pytest.raises(Role.DoesNotExist):
            update_forum_role(self.course.id, user, 'robot-not-a-real-role', 'allow')

    def test_bad_mode(self):
        user = UserFactory()
        with pytest.raises(ValueError):
            update_forum_role(self.course.id, user, FORUM_ROLE_MODERATOR, 'robot-not-a-mode')
