#pragma once
#include "platform.h"
#include "sqlite_helper.h"

#include <absl/base/thread_annotations.h>
#include <absl/strings/str_cat.h>
#include <string_view>

#include <string>
#include <vector>

namespace securefs
{

namespace internal
{
    class ABSL_LOCKABLE LookupTableBase
    {
    public:
        void lock() ABSL_EXCLUSIVE_LOCK_FUNCTION(*this) ABSL_NO_THREAD_SAFETY_ANALYSIS
        {
            db_.mutex().Lock();
            begin();
        }

        void unlock() ABSL_UNLOCK_FUNCTION(*this) ABSL_NO_THREAD_SAFETY_ANALYSIS
        {
            finish();
            db_.mutex().Unlock();
        }

    protected:
        SQLiteDB db_ ABSL_GUARDED_BY(*this);

    protected:
        void begin() ABSL_EXCLUSIVE_LOCKS_REQUIRED(*this);
        void finish() noexcept ABSL_EXCLUSIVE_LOCKS_REQUIRED(*this);
    };
}    // namespace internal

///@brief Wraps a SQLite database, to store the mapping between the keyed hash and encrypted name.
/// The table is needed when the file name component is so long that its encrypted version no longer
/// fits on most filesystems.
class ABSL_LOCKABLE LongNameLookupTable : public internal::LookupTableBase
{
public:
    LongNameLookupTable(const std::string& filename, bool readonly);
    ~LongNameLookupTable();

    std::string lookup(std::string_view keyed_hash) ABSL_EXCLUSIVE_LOCKS_REQUIRED(*this);
    void update_mapping(std::string_view keyed_hash, std::string_view encrypted_long_name)
        ABSL_EXCLUSIVE_LOCKS_REQUIRED(*this);
    void remove_mapping(std::string_view keyed_hash) ABSL_EXCLUSIVE_LOCKS_REQUIRED(*this);

    std::vector<std::string> list_hashes() ABSL_EXCLUSIVE_LOCKS_REQUIRED(*this);
};

///@brief Only used in `rename` operations, when two operations need to be atomic together.
class ABSL_LOCKABLE DoubleLongNameLookupTable : public internal::LookupTableBase
{
public:
    DoubleLongNameLookupTable(const std::string& from_dir_db, const std::string& to_dir_db);

    void remove_mapping_from_from_db(std::string_view keyed_hash)
        ABSL_EXCLUSIVE_LOCKS_REQUIRED(*this);

    void update_mapping_to_to_db(std::string_view keyed_hash, std::string_view encrypted_long_name)
        ABSL_EXCLUSIVE_LOCKS_REQUIRED(*this);

private:
    bool is_same_db_;
};
}    // namespace securefs
