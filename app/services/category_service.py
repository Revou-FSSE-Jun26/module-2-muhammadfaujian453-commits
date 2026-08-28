"""Category service — business logic for product categories."""
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models import Categories
from app.utils import db


def create_category(validated_data):
    try:
        category = Categories(name=validated_data['name'], description=validated_data.get('description'))
        db.session.add(category)
        db.session.commit()
        return category, None
    except IntegrityError:
        db.session.rollback()
        return None, {"message": f"Category name '{validated_data['name']}' already exists on the system!", "status_code": 409}
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return None, {"message": "A database error occurred processing your request.", "status_code": 500}


def get_all_categories():
    return Categories.query.all()


def update_category(category_id, validated_data):
    category = db.session.get(Categories, category_id)
    if not category:
        return None, {"message": "Category not found!", "status_code": 404}

    try:
        if 'name' in validated_data:
            new_name = validated_data['name']
            if new_name != category.name:
                if Categories.query.filter_by(name=new_name).first():
                    return None, {"message": f"Category name '{new_name}' already exists!", "status_code": 409}
                category.name = new_name
        if 'description' in validated_data:
            category.description = validated_data.get('description')

        db.session.commit()
        return category, None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return None, {"message": "A database error occurred processing your request.", "status_code": 500}


def delete_category(category_id):
    category = db.session.get(Categories, category_id)
    if not category:
        return None, {"message": "Category not found!", "status_code": 404}

    try:
        deleted_name = category.name
        db.session.delete(category)
        db.session.commit()
        return deleted_name, None
    except IntegrityError:
        db.session.rollback()
        return None, {"message": "Cannot delete this category because there are products currently assigned to it.", "status_code": 409}
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return None, {"message": "A database error occurred processing your request.", "status_code": 500}