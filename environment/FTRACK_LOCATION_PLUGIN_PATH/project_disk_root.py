import os
import platform

import ftrack


class ProjectDiskStructure(ftrack.StandardStructure):

    def getResourceIdentifier(self, entity):

        project = entity.getParents()[-1]

        system_name = platform.system().lower()
        if system_name != "windows":
            system_name = "unix"

        mount = ftrack.Disk(project.get("diskid")).get(system_name)
        parts = [mount, project.get("root")]

        if not entity.isContainer():
            container = entity.getContainer()

            if container:
                # Get resource identifier for container.
                containerPath = self.getResourceIdentifier(container)

                if container.isSequence():
                    # Strip the sequence component expression from the parent
                    # container and back the correct filename, i.e.
                    # /sequence/component/sequence_component_name.0012.exr.
                    name = '{0}.{1}{2}'.format(
                        container.getName(), entity.getName(),
                        entity.getFileType()
                    )
                    parts += [
                        os.path.dirname(containerPath),
                        self.sanitiseForFilesystem(name)
                    ]

                else:
                    # Container is not a sequence component so add it as a
                    # normal component inside the container.
                    name = entity.getName() + entity.getFileType()
                    parts = +[
                        containerPath, self.sanitiseForFilesystem(name)
                    ]

            else:
                # File component does not have a container, construct name from
                # component name and file type.
                parts += self._getParts(entity)
                name = entity.getName() + entity.getFileType()
                parts.append(self.sanitiseForFilesystem(name))

        elif entity.isSequence():
            # Create sequence expression for the sequence component and add it
            # to the parts.
            parts += self._getParts(entity)
            sequenceExpression = self._getSequenceExpression(entity)
            parts.append(
                '{0}.{1}{2}'.format(
                    self.sanitiseForFilesystem(entity.getName()),
                    sequenceExpression,
                    self.sanitiseForFilesystem(entity.getFileType())
                )
            )

        elif entity.isContainer():
            # Add the name of the container to the resource identifier parts.
            parts += self._getParts(entity)
            parts.append(self.sanitiseForFilesystem(entity.getName()))

        else:
            raise NotImplementedError(
                'Cannot generate resource identifier for unsupported '
                'entity {0!r}'.format(entity)
            )

        path = self.pathSeparator.join(parts)
        return path.replace("//", "/")


class ResourceIdentifierTransformer(object):

    def __init__(self):

        super(ResourceIdentifierTransformer, self).__init__()

    def encode(self, resource_identifier, context=None):

        return resource_identifier.replace(
            self.get_project_directory(context), ""
        )

    def decode(self, resource_identifier, context=None):

        return os.path.join(
            self.get_project_directory(context), resource_identifier
        ).replace("\\", "/")

    def get_project_directory(self, context):

        project = context["component"].getParents()[-1]

        system_name = platform.system().lower()
        if system_name != "windows":
            system_name = "unix"

        return os.path.join(
            ftrack.Disk(project.get("diskid")).get(system_name),
            project.get("root"), ""
        ).replace("\\", "/")


def register(registry, **kw):

    location = ftrack.ensureLocation("project.disk.root")
    location.setAccessor(ftrack.DiskAccessor(prefix=""))
    location.setStructure(ProjectDiskStructure())
    location.setResourceIdentifierTransformer(ResourceIdentifierTransformer())

    registry.add(location)
