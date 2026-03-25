from app.domain.entities import WorkspaceRole


def test_role_hierarchy():
    assert WorkspaceRole.OWNER.has_minimum_role(WorkspaceRole.OWNER)
    assert WorkspaceRole.OWNER.has_minimum_role(WorkspaceRole.VIEWER)
    assert WorkspaceRole.ADMIN.has_minimum_role(WorkspaceRole.EDITOR)
    assert not WorkspaceRole.EDITOR.has_minimum_role(WorkspaceRole.ADMIN)
    assert not WorkspaceRole.VIEWER.has_minimum_role(WorkspaceRole.EDITOR)


def test_can_manage_members():
    assert WorkspaceRole.OWNER.can_manage_members()
    assert WorkspaceRole.ADMIN.can_manage_members()
    assert not WorkspaceRole.EDITOR.can_manage_members()
    assert not WorkspaceRole.VIEWER.can_manage_members()


def test_can_edit_resources():
    assert WorkspaceRole.OWNER.can_edit_resources()
    assert WorkspaceRole.ADMIN.can_edit_resources()
    assert WorkspaceRole.EDITOR.can_edit_resources()
    assert not WorkspaceRole.VIEWER.can_edit_resources()
